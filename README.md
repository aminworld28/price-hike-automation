# price-hike-automation

**Update hundreds of product prices in a web admin portal, from an Excel sheet, in minutes, even when the portal has no bulk-update feature and you don't control it.**

Many companies run their e-commerce or ordering platform through a third-party vendor. You can edit prices in the vendor's admin screen, but only one product at a time, and the "Import Excel" button may not cover price updates. Then leadership says *"prices go up tomorrow, on every platform."*

This tool does what a person would do, only faster and without typos. For every row in your price sheet it:

```
search the product code -> open Edit -> set the new price
        -> fill Type / Service if they're empty -> click Update -> reopen and verify
```

No API access, no vendor involvement, no database access. Just a browser session logged in with your own account.

---

## Try it in 3 minutes (no real system needed)

The repo includes a **fake admin portal** and a **dummy price sheet**, so you can watch the whole flow safely.

```bash
pip install -r requirements.txt
playwright install chromium

python make_sample_sheet.py          # creates data/sample_price_sheet.xlsx (a +10% hike)
python mock_portal/app.py            # starts the fake portal on http://127.0.0.1:5000
```

In a second terminal:

```bash
python update_prices.py                        # 1. DRY RUN: fills the forms, saves nothing
python update_prices.py --live --only B001     # 2. save ONE product, check it in the portal
python update_prices.py --live                 # 3. save everything
```

Open http://127.0.0.1:5000/products to see the new prices. Each run writes a `prices_log_<timestamp>.csv`.

The dummy data includes the awkward cases on purpose: products with no Type/Service selected (the portal refuses to save those), a beverage, veg and non-veg names, and a code that doesn't exist in the portal (`X999` shows up as `NOT_FOUND`).

---

## Use it on your real portal

1. Copy `config.json` to `config.real.json` (it's git-ignored) and run with `--config config.real.json`.
2. Put your sheet in `data/` and set `excel_file`, `header_row` and `columns` (0-based column positions for category, code, name, new price).
3. Point `base_url` and `search_url` at your portal. `{code}` is replaced by each product code.
4. Set `"login_pause": true`. The script opens a browser, **you log in yourself** (passwords and 2FA never touch the script), then press Enter in the terminal. The login is remembered in `profile_dir`.
5. Adjust the `selectors` so they match your pages. In Chrome, right-click an element, **Inspect**, then right-click the HTML and choose **Copy > Copy selector**:

| Config key | What it points to |
|---|---|
| `result_rows` | rows of the search-results table |
| `code_cell_index` / `name_cell_index` | which column (0-based) holds the code / name |
| `edit_link` | the Edit link inside a row |
| `price_input` | the price box on the Edit page |
| `radios` | all radio buttons on the Edit page |
| `submit_button_text` | text on the save button |

6. Check `radio_layout`. The script picks radio buttons **by position** (Status, Type, Only-For-Deal, Service in the demo). Set `expected_count` and the index of each option to match your form. If a page doesn't have that many radios, the item is logged as `ERROR` and skipped instead of clicking the wrong thing.
7. Always do it in this order: **dry run, then `--live --only <one code>`, then everything.**

---

## The Type / Service rules

Some portals refuse to save a product unless *Type* and *Service* are selected. Products that were never filled in silently block the update. This script fills them in **only when nothing is selected** (existing choices are kept):

| Field | Rule |
|---|---|
| Type | Category contains "bever" (configurable): **None** · name contains the word "Veg": **Veg** · everything else: **Non Veg** |
| Service | **All** (set `force_service_all` to `true` to overwrite Delivery/Pickup too) |

"Non Veg" and "Non-Veg" are not mistaken for Veg. Note that rules are keyword-based: *"Paneer Royale Burger"* becomes Non Veg because the name has no "Veg". Edit `wanted_type()` in `update_prices.py` to fit your menu (for example, add `paneer`).

---

## Built-in safety

- **Dry run by default.** Nothing is saved unless you pass `--live`.
- **Exact code matching.** A search for `K01` also returns `K011`; only the exact code is edited.
- **Verified saves.** After clicking Update it reopens the product and checks the price, Type and Service really stuck.
- **Safe to re-run.** Products already at the new price show `ALREADY` and are skipped. If it stops halfway, run it again.
- **One bad item never stops the batch.** Failures are logged and the run continues.
- **A CSV log for every run**, so you can fix exceptions by hand.

| Status | Meaning |
|---|---|
| `UPDATED` | saved and verified |
| `DRY_RUN` | would have changed (see the note column) |
| `ALREADY` | already correct, skipped |
| `NOT_FOUND` | code not found in the portal |
| `VERIFY_FAIL` | clicked Update but the values didn't stick: check by hand |
| `ERROR` | unexpected page or exception: check by hand |

While it runs, don't click inside the automated browser window, and keep the PC awake.

---

## Limitations

- It drives the portal's web UI, so a redesign of the pages can break the selectors in `config`.
- Sites with CAPTCHAs or aggressive bot protection may not work.
- It was designed around a search-then-edit flow; other layouts need code changes.

## Responsible use

Only automate systems you are **authorised** to use, with your **own** account, and check your vendor's terms. This tool just repeats the clicks you're already allowed to make by hand. Test on a few items first: a wrong price list pushed to every outlet is easy to create at speed.

## Files

```
update_prices.py        the automation
config.json             settings + selectors (demo values)
make_sample_sheet.py    builds the dummy Excel sheet
mock_portal/            fake admin portal (Flask) + dummy catalogue
data/                   sample_price_sheet.xlsx
```

MIT licensed.

