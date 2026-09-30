#!/usr/bin/env python3
"""
Bulk price updater for web admin portals that have no bulk-price feature.

It reads a price sheet (Excel) and, for every product code, does what a person would:
search the code -> open Edit -> set price -> fill Type/Service if empty -> Update -> verify.

Safe by default: it only *previews* unless you pass --live.

    python update_prices.py                      # dry run (nothing is saved)
    python update_prices.py --live --only B001   # save one product, check it by hand
    python update_prices.py --live               # save everything in the sheet
"""
import argparse
import csv
import datetime
import json
import re
import time
from collections import Counter
from urllib.parse import quote, urljoin

import pandas as pd
from playwright.sync_api import sync_playwright

# "Veg" as a separate word, but not "Non Veg" / "Non-Veg"
VEG_RE = re.compile(r"(?<!non )(?<!non-)\bveg\b", re.I)


def wanted_type(category, names, beverage_kw):
    """Beverage -> None | name has the word Veg -> Veg | everything else -> Non Veg"""
    if beverage_kw.lower() in str(category).lower():
        return "None"
    if any(VEG_RE.search(str(n)) for n in names):
        return "Veg"
    return "Non Veg"


def load_items(cfg):
    c = cfg["columns"]
    df = pd.read_excel(cfg["excel_file"], header=cfg["header_row"] - 1)
    df = df.iloc[:, [c["category"], c["code"], c["name"], c["price"]]]
    df.columns = ["category", "code", "name", "price"]
    df = df.dropna(subset=["code", "price"])
    df["code"] = df["code"].astype(str).str.strip()
    df["price"] = df["price"].astype(float).round().astype(int)
    return list(df.itertuples(index=False, name=None))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--live", action="store_true", help="actually click Update (default is a dry run)")
    ap.add_argument("--only", help="comma-separated product codes to process, e.g. B001,D002")
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))
    sel, lay = cfg["selectors"], cfg["radio_layout"]
    type_idx, svc_idx = lay["type"], lay["service"]
    type_group, svc_group = list(type_idx.values()), list(svc_idx.values())
    dry_run = not args.live

    items = load_items(cfg)
    if args.only:
        wanted = {c.strip() for c in args.only.split(",")}
        items = [i for i in items if i[1] in wanted]
    print(f"{len(items)} items to process | {'DRY RUN (nothing saved)' if dry_run else 'LIVE'}")

    log_path = f"prices_log_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
    rows = []

    def log(code, status, old="", new="", note=""):
        rows.append([code, status, old, new, note])
        print(f"{code:8} {status:11} {old} -> {new} {note}")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(cfg["profile_dir"], headless=cfg["headless"])
        page = ctx.new_page()
        page.goto(cfg["base_url"])
        if cfg["login_pause"]:
            input("Log in in the opened browser, then press Enter here... ")

        for category, code, sheet_name, new_price in items:
            try:
                page.goto(cfg["base_url"] + cfg["search_url"].format(code=quote(code)))
                page.wait_for_load_state("networkidle")

                # search can partial-match (K01 also finds K011), so keep exact code matches only
                matches = []
                trs = page.locator(sel["result_rows"])
                for i in range(trs.count()):
                    tr = trs.nth(i)
                    tds = tr.locator("td")
                    if tds.count() <= max(sel["code_cell_index"], sel["name_cell_index"]):
                        continue
                    if tds.nth(sel["code_cell_index"]).inner_text().strip() == code:
                        href = tr.locator(sel["edit_link"]).first.get_attribute("href")
                        matches.append((urljoin(cfg["base_url"], href),
                                        tds.nth(sel["name_cell_index"]).inner_text().strip()))
                if not matches:
                    log(code, "NOT_FOUND")
                    continue

                for url, portal_name in matches:
                    page.goto(url)
                    page.wait_for_load_state("networkidle")

                    radios = page.locator(sel["radios"])
                    if radios.count() != lay["expected_count"]:
                        log(code, "ERROR", note=f"unexpected form layout ({radios.count()} radios)")
                        continue

                    price_box = page.locator(sel["price_input"]).first
                    old = price_box.input_value()
                    want_type = wanted_type(category, [sheet_name, portal_name], cfg["beverage_category_keyword"])
                    changes = []

                    if int(float(old)) != new_price:
                        price_box.fill(str(new_price))
                        changes.append("price")
                    if not any(radios.nth(i).is_checked() for i in type_group):
                        radios.nth(type_idx[want_type]).check(force=True)
                        changes.append(f"type={want_type}")
                    if cfg["force_service_all"] or not any(radios.nth(i).is_checked() for i in svc_group):
                        radios.nth(svc_idx["All"]).check(force=True)
                        changes.append("service=All")

                    if not changes:
                        log(code, "ALREADY", old, new_price)
                        continue
                    note = ",".join(changes) + (" | multiple rows" if len(matches) > 1 else "")
                    if dry_run:
                        log(code, "DRY_RUN", old, new_price, note)
                        continue

                    page.get_by_role("button", name=sel["submit_button_text"]).click()
                    page.wait_for_load_state("networkidle")

                    # reopen and verify it really saved
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    radios = page.locator(sel["radios"])
                    saved = page.locator(sel["price_input"]).first.input_value()
                    ok = (int(float(saved)) == new_price
                          and any(radios.nth(i).is_checked() for i in type_group)
                          and any(radios.nth(i).is_checked() for i in svc_group))
                    log(code, "UPDATED" if ok else "VERIFY_FAIL", old, saved, note)
                time.sleep(0.3)
            except Exception as e:  # one bad item must not stop the batch
                log(code, "ERROR", note=str(e)[:120])
        ctx.close()

    with open(log_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "status", "old_price", "new_price", "note"])
        w.writerows(rows)
    summary = ", ".join(f"{k}={v}" for k, v in Counter(r[1] for r in rows).items())
    print(f"\nDone. {summary}\nLog: {log_path}")


if __name__ == "__main__":
    main()
