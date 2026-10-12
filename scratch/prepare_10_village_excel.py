import openpyxl
from pathlib import Path

src_path = "C:/Users/Admin/.gemini/antigravity/brain/00fe1a6c-ff00-4d9d-a57e-84b67982ddd1/.user_uploaded/media_1791280815428.xlsx"
src_wb = openpyxl.load_workbook(src_path, data_only=True)
src_ws = src_wb.active

dst_wb = openpyxl.Workbook()
dst_ws = dst_wb.active
dst_ws.title = src_ws.title

# Header
dst_ws.append([src_ws.cell(1, c).value for c in range(1, src_ws.max_column + 1)])

# Copy 10 rows (rows 85 to 95 in the source sheet which contain Davadra, Motal, Antarnes, Bamroli, etc.)
for r in range(86, 96):
    dst_ws.append([src_ws.cell(r, c).value for c in range(1, src_ws.max_column + 1)])

dst_path = Path("scratch/test_10_villages.xlsx")
dst_wb.save(str(dst_path))
print(f"Created {dst_path} with 10 village rows.")

for r in range(1, 12):
    v_name = dst_ws.cell(r, 7).value
    v_code = dst_ws.cell(r, 8).value
    print(f"Row {r}: {v_name} ({v_code})")
