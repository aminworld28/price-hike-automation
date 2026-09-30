"""Generates data/sample_price_sheet.xlsx: a 10% price hike over the mock catalogue.
Layout mirrors a typical 'price hike' sheet: row 1 blank, row 2 headers, data from row 3."""
from pathlib import Path
from openpyxl import Workbook
from mock_portal.seed import PRODUCTS

out = Path("data/sample_price_sheet.xlsx")
out.parent.mkdir(exist_ok=True)

wb = Workbook()
ws = wb.active
ws.title = "Sheet1"
ws.append([])
ws.append(["Category", "Code", "Deal Name", "Revised Price (with tax)", "Revised Price (w/o tax)"])
for p in PRODUCTS:
    new = int(round(p["price"] * 1.10 / 5) * 5)       # +10%, rounded to nearest 5
    ws.append([p["category"], p["code"], p["name"], new, round(new / 1.13, 4)])
ws.append(["Snacks", "X999", "Discontinued Item (not in portal)", 199, round(199 / 1.13, 4)])  # shows NOT_FOUND
ws.column_dimensions["C"].width = 36
wb.save(out)
print(f"wrote {out}")
