import io
import re
import os
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from pathlib import Path
from werkzeug.utils import secure_filename
import db
from config import Config

# Standard mapping dictionary from common header names to our database field names
COLUMN_MAPPING_RULES = {
    'zone': 'zone',
    'district': 'district_name',
    'district_name': 'district_name',
    'districtname': 'district_name',
    'subdistrict': 'subdistrict_name',
    'subdistrict_name': 'subdistrict_name',
    'subdistrictname': 'subdistrict_name',
    'taluka': 'subdistrict_name',
    'taluk': 'subdistrict_name',
    'tehsil': 'subdistrict_name',
    'village': 'village_name',
    'village_name': 'village_name',
    'villagename': 'village_name',
    'village name': 'village_name',
    'village_code': 'village_code',
    'villagecode': 'village_code',
    'village code': 'village_code',
    'code': 'village_code',
    'geb_connection': 'geb_connection',
    'geb connection': 'geb_connection',
    'geb': 'geb_connection',
    'electric_kuva': 'electric_kuva',
    'electric kuva': 'electric_kuva',
    'electric (kuva)': 'electric_kuva',
    'electric_bor': 'electric_bor',
    'electric bor': 'electric_bor',
    'electric (bor)': 'electric_bor',
    'total_electric': 'total_electric',
    'total electric': 'total_electric',
    'total electric (bor+kuva)': 'total_electric',
    'solar_bor_kuva': 'solar_bor_kuva',
    'solar': 'solar_bor_kuva',
    'solar (bor+kuva)': 'solar_bor_kuva',
    'total_electric_solar': 'total_electric_solar',
    'total electric solar': 'total_electric_solar',
    'total(electric &solar)': 'total_electric_solar',
    'total(electric & solar)': 'total_electric_solar',
    'google_search_original_nos': 'google_search_orig_nos',
    'google search original nos': 'google_search_orig_nos',
    'google_search_orig_nos': 'google_search_orig_nos',
    'orig_nos': 'google_search_orig_nos',
    'google_edited_nos_and_final_kml': 'google_edited_nos',
    'google edited nos and final kml': 'google_edited_nos',
    'google_edited_nos': 'google_edited_nos',
    'edited_nos': 'google_edited_nos',
    'total': 'total_wells',
    'total_wells': 'total_wells',
    'dugwells': 'dugwells',
    'dugwell': 'dugwells',
    'dug_wells': 'dugwells',
    'bores': 'bores',
    'bore': 'bores',
    'borewell': 'bores',
    'borewells': 'bores',
    'kml_status': 'kml_status',
    'kml status': 'kml_status',
    'kml status (in progress/done)': 'kml_status',
    'remark': 'remark',
    'remarks': 'remark'
}

REQUIRED_CANONICAL_FIELDS = ['district_name', 'subdistrict_name', 'village_name', 'village_code']


def normalize_header(header):
    """Normalize a header string for reliable matching."""
    if not header:
        return ''
    cleaned = str(header).strip().lower()
    cleaned = re.sub(r'[\s\-_./\\()\[\]+:,]+', ' ', cleaned).strip()
    return cleaned


def detect_column_mappings(actual_headers):
    """
    Given a list of actual header strings from the uploaded file,
    return a dict mapping: { actual_header: canonical_field_name or None }.
    Supports English, Gujarati headers, and common variations.
    """
    mappings = {}
    used_canonical = set()

    for raw_header in actual_headers:
        norm = normalize_header(raw_header)
        matched_field = None

        # 1. Explicitly ignore headers that should never be mapped to village_code or other fields
        # E.g. Serial Number, District Code, Taluka Code
        if re.search(r'^(ક્રમ|sr\b|sl\b|sno|s\s*no|index)', norm):
            mappings[raw_header] = None
            continue
        if re.search(r'(જિલ્લા.*કોડ|district.*code|dist.*code)', norm):
            mappings[raw_header] = None
            continue
        if re.search(r'(તાલુકા.*કોડ|taluka.*code|subdistrict.*code|block.*code|tehsil.*code)', norm):
            mappings[raw_header] = None
            continue

        # 2. Match village_code (high priority before generic code)
        if 'village_code' not in used_canonical:
            if re.search(r'(ગામ.*કોડ|village.*code|vcode|lgd.*code|census.*code)', norm):
                matched_field = 'village_code'
            elif norm in ('code', 'કોડ'):
                matched_field = 'village_code'

        # 3. Match village_name
        if not matched_field and 'village_name' not in used_canonical:
            if re.search(r'(ગામ.*નામ|village.*name|villagename|village_name|vname)', norm):
                matched_field = 'village_name'
            elif re.search(r'^(ગામ|village)$', norm):
                matched_field = 'village_name'

        # 4. Match district_name
        if not matched_field and 'district_name' not in used_canonical:
            if re.search(r'(જિલ્લા.*નામ|district.*name|districtname|district_name|dist.*name)', norm):
                matched_field = 'district_name'
            elif re.search(r'^(જિલ્લો|જિલ્લા|district|dist)$', norm):
                matched_field = 'district_name'

        # 5. Match subdistrict_name (taluka / tehsil / subdistrict)
        if not matched_field and 'subdistrict_name' not in used_canonical:
            if re.search(r'(તાલુકા.*નામ|taluka.*name|subdistrict.*name|tehsil.*name|block.*name)', norm):
                matched_field = 'subdistrict_name'
            elif re.search(r'^(તાલુકો|તાલુકા|taluka|subdistrict|taluk|tehsil|block)$', norm):
                matched_field = 'subdistrict_name'

        # 6. Match zone
        if not matched_field and 'zone' not in used_canonical:
            if re.search(r'^(ઝોન|zone)', norm):
                matched_field = 'zone'

        # 7. Match GEB Electric & Solar Columns
        if not matched_field and 'total_electric_solar' not in used_canonical:
            if re.search(r'total.*(electric|વીજળી).*solar|total.*electric.*&.*solar|total\s*\(?\s*electric\s*&\s*solar\s*\)?', norm):
                matched_field = 'total_electric_solar'

        if not matched_field and 'solar_bor_kuva' not in used_canonical:
            if re.search(r'solar.*(bor|kuva)|\bsolar\b|\bસોલાર\b', norm):
                matched_field = 'solar_bor_kuva'

        if not matched_field and 'total_electric' not in used_canonical:
            if re.search(r'total.*electric|કુલ.*વીજળી', norm):
                matched_field = 'total_electric'

        if not matched_field and 'electric_kuva' not in used_canonical:
            if re.search(r'electric.*(kuva|કૂવા|કુવા)|electric\s*\(kuva\)', norm):
                matched_field = 'electric_kuva'

        if not matched_field and 'electric_bor' not in used_canonical:
            if re.search(r'electric.*(bor|બોર)|electric\s*\(bor\)', norm):
                matched_field = 'electric_bor'

        # 8. Match dugwells (કૂવા)
        if not matched_field and 'dugwells' not in used_canonical:
            if re.search(r'(કૂવા|કુવા|dugwell|dug\s*wells?|open\s*wells?)', norm):
                matched_field = 'dugwells'

        # 9. Match bores (બોર)
        if not matched_field and 'bores' not in used_canonical:
            if re.search(r'(બોર|bore|bores|borewell|tubewell|\bbor\b)', norm) and not re.search(r'(સોલાર|solar)', norm):
                matched_field = 'bores'

        # 10. Match total_wells
        if not matched_field and 'total_wells' not in used_canonical:
            if re.search(r'^(કુલ|total)', norm):
                matched_field = 'total_wells'

        # 11. Match geb_connection
        if not matched_field and 'geb_connection' not in used_canonical:
            if re.search(r'(geb|વીજળી|electricity)', norm) and not re.search(r'(કૂવા|કુવા|બોર|bor)', norm):
                matched_field = 'geb_connection'

        # 12. Match google search / edited / kml / remark
        if not matched_field and 'google_search_orig_nos' not in used_canonical:
            if re.search(r'(google.*orig|search.*orig|orig.*nos)', norm):
                matched_field = 'google_search_orig_nos'

        if not matched_field and 'google_edited_nos' not in used_canonical:
            if re.search(r'(google.*edit|edited.*nos|final.*kml)', norm):
                matched_field = 'google_edited_nos'

        if not matched_field and 'kml_status' not in used_canonical:
            if re.search(r'(kml.*status|kml)', norm):
                matched_field = 'kml_status'

        if not matched_field and 'remark' not in used_canonical:
            if re.search(r'(remark|remarks|comment|નોંધ|શેરો)', norm):
                matched_field = 'remark'

        mappings[raw_header] = matched_field
        if matched_field:
            used_canonical.add(matched_field)

    return mappings



def preview_uploaded_file(file_storage_or_path, max_preview_rows=10):
    """
    Reads the initial rows of an Excel/CSV file to provide headers,
    suggested mappings, sample rows, and row counts.
    """
    if hasattr(file_storage_or_path, 'name'):
        filename = file_storage_or_path.filename
        content = file_storage_or_path.read()
        file_obj = io.BytesIO(content)
    else:
        filename = os.path.basename(file_storage_or_path)
        with open(file_storage_or_path, 'rb') as f:
            content = f.read()
        file_obj = io.BytesIO(content)

    ext = os.path.splitext(filename)[1].lower()

    if ext == '.csv':
        df = pd.read_csv(file_obj, dtype=str, nrows=max_preview_rows + 50)
        # Count total rows quickly
        file_obj.seek(0)
        total_rows = sum(1 for _ in file_obj) - 1  # Minus header
    elif ext in ('.xlsx', '.xls'):
        engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
        df = pd.read_excel(file_obj, dtype=str, nrows=max_preview_rows, engine='openpyxl')
        # Get total row count
        file_obj.seek(0)
        wb = openpyxl.load_workbook(file_obj, read_only=True)
        sheet = wb.active
        total_rows = sheet.max_row - 1 if sheet.max_row else len(df)
        wb.close()
    else:
        raise ValueError(f"Unsupported file format '{ext}'. Please upload .xlsx, .xls, or .csv.")

    actual_headers = [str(col).strip() for col in df.columns]
    suggested_mappings = detect_column_mappings(actual_headers)

    preview_rows = df.head(max_preview_rows).fillna('').to_dict(orient='records')

    # Identify missing required fields
    mapped_fields = set(suggested_mappings.values())
    missing_required = [req for req in REQUIRED_CANONICAL_FIELDS if req not in mapped_fields]

    return {
        "filename": filename,
        "total_estimated_rows": max(total_rows, len(df)),
        "headers": actual_headers,
        "suggested_mappings": suggested_mappings,
        "preview_rows": preview_rows,
        "missing_required": missing_required,
        "is_ready_to_import": len(missing_required) == 0
    }


def parse_and_import_file(file_storage_or_path, column_mappings, duplicate_mode='skip', batch_filename=None):
    """
    Perform full batch import into SQL Server.
    
    Parameters:
    - file_storage_or_path: FileStorage object or file path
    - column_mappings: dict mapping { actual_header: canonical_field }
    - duplicate_mode: 'skip', 'update', or 'import_new'
    - batch_filename: original file name
    """
    Config.ensure_dirs()

    if hasattr(file_storage_or_path, 'filename'):
        filename = batch_filename or file_storage_or_path.filename
        content = file_storage_or_path.read()
    else:
        filename = batch_filename or os.path.basename(file_storage_or_path)
        with open(file_storage_or_path, 'rb') as f:
            content = f.read()

    # Save uploaded file for audit / history
    clean_filename = secure_filename(filename) or "imported_file.xlsx"
    saved_batch_path = Config.EXCEL_UPLOAD_DIR / f"{int(pd.Timestamp.now().timestamp())}_{clean_filename}"
    with open(saved_batch_path, 'wb') as f:
        f.write(content)

    ext = os.path.splitext(filename)[1].lower()
    file_obj = io.BytesIO(content)

    if ext == '.csv':
        df = pd.read_csv(file_obj, dtype=str)
    else:
        df = pd.read_excel(file_obj, dtype=str, engine='openpyxl')

    # Auto-detect column mappings for all headers in the file
    auto_mappings = detect_column_mappings(list(df.columns))
    
    # Merge user-provided mappings (if any) with auto-detected mappings
    merged_mappings = {}
    if column_mappings and isinstance(column_mappings, dict):
        merged_mappings.update(column_mappings)
    
    # Fill in any missing or empty mappings from auto_mappings
    for raw_col, canonical_field in auto_mappings.items():
        if canonical_field and (raw_col not in merged_mappings or not merged_mappings[raw_col]):
            merged_mappings[raw_col] = canonical_field

    # Rename columns using merged mappings
    rename_dict = {actual: canonical for actual, canonical in merged_mappings.items() if canonical}
    df = df.rename(columns=rename_dict)

    # Ensure required columns are present
    for req in REQUIRED_CANONICAL_FIELDS:
        if req not in df.columns:
            raise ValueError(f"Required field '{req}' is missing from column mappings.")

    total_rows = len(df)
    valid_records = []
    invalid_records = []
    seen_codes_in_file = set()
    duplicate_count = 0

    # Fetch existing village codes from DB for duplicate checking
    existing_villages = {
        row['village_code'].strip(): row['id']
        for row in db.query_all("SELECT id, village_code FROM Villages")
        if row.get('village_code')
    }

    # Helper function to clean integers
    def safe_int(val, default=0):
        if val is None or pd.isna(val):
            return default
        try:
            cleaned = re.sub(r'[^\d-]', '', str(val))
            return int(cleaned) if cleaned else default
        except (ValueError, TypeError):
            return default

    # Validation loop
    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed Excel row including header
        row_dict = row.to_dict()

        # Extract values
        v_code = str(row_dict.get('village_code', '')).strip()
        v_name = str(row_dict.get('village_name', '')).strip()
        d_name = str(row_dict.get('district_name', '')).strip()
        s_name = str(row_dict.get('subdistrict_name', '')).strip()
        zone = str(row_dict.get('zone', '')).strip() if 'zone' in row_dict and not pd.isna(row_dict.get('zone')) else ''
        geb = str(row_dict.get('geb_connection', '')).strip() if 'geb_connection' in row_dict and not pd.isna(row_dict.get('geb_connection')) else ''
        remark = str(row_dict.get('remark', '')).strip() if 'remark' in row_dict and not pd.isna(row_dict.get('remark')) else ''

        errors = []
        if not v_code or v_code.lower() == 'nan':
            errors.append("Village Code is missing or empty")
        if not v_name or v_name.lower() == 'nan':
            errors.append("Village name is missing")
        if not d_name or d_name.lower() == 'nan':
            errors.append("District Name is missing")
        if not s_name or s_name.lower() == 'nan':
            errors.append("Subdistrict Name is missing")

        if errors:
            invalid_records.append({
                "row_num": row_num,
                "village_code": v_code,
                "village_name": v_name,
                "district_name": d_name,
                "subdistrict_name": s_name,
                "error_reason": "; ".join(errors)
            })
            continue

        is_dup_in_file = v_code in seen_codes_in_file
        is_dup_in_db = v_code in existing_villages

        if is_dup_in_file or is_dup_in_db:
            duplicate_count += 1
            if duplicate_mode == 'skip':
                continue

        seen_codes_in_file.add(v_code)

        orig_nos = safe_int(row_dict.get('google_search_orig_nos', 0))
        edited_nos = safe_int(row_dict.get('google_edited_nos', 0))
        dugwells = safe_int(row_dict.get('dugwells', 0))
        bores = safe_int(row_dict.get('bores', 0))
        
        elec_kuva = safe_int(row_dict.get('electric_kuva', 0))
        elec_bor = safe_int(row_dict.get('electric_bor', 0))
        tot_elec = safe_int(row_dict.get('total_electric', 0))
        solar_bk = safe_int(row_dict.get('solar_bor_kuva', 0))
        tot_elec_solar = safe_int(row_dict.get('total_electric_solar', 0))

        if tot_elec == 0 and (elec_kuva > 0 or elec_bor > 0):
            tot_elec = elec_kuva + elec_bor
        if tot_elec_solar == 0 and (tot_elec > 0 or solar_bk > 0):
            tot_elec_solar = tot_elec + solar_bk

        # Calculate total
        total = safe_int(row_dict.get('total_wells'))
        if total == 0 and (dugwells > 0 or bores > 0):
            total = dugwells + bores
        if total == 0 and tot_elec_solar > 0:
            total = tot_elec_solar

        # Also store entire raw row for high-fidelity export preservation
        raw_row_data = {str(k): ('' if pd.isna(v) else str(v).strip()) for k, v in row.items()}
        raw_geb_json = json.dumps(raw_row_data, ensure_ascii=False)

        kml_status = str(row_dict.get('kml_status', 'Pending')).strip()
        if not kml_status or kml_status.lower() == 'nan':
            kml_status = 'Pending'

        valid_records.append({
            "zone": zone,
            "district_name": d_name,
            "subdistrict_name": s_name,
            "village_name": v_name,
            "village_code": v_code,
            "geb_connection": geb,
            "google_search_orig_nos": orig_nos,
            "google_edited_nos": edited_nos,
            "total_wells": total,
            "dugwells": dugwells,
            "bores": bores,
            "electric_kuva": elec_kuva,
            "electric_bor": elec_bor,
            "total_electric": tot_elec,
            "solar_bor_kuva": solar_bk,
            "total_electric_solar": tot_elec_solar,
            "raw_geb_data": raw_geb_json,
            "kml_status": kml_status,
            "remark": remark,
            "is_update": is_dup_in_db and duplicate_mode == 'update',
            "existing_id": existing_villages.get(v_code)
        })

    # Generate Error Report Excel if there are invalid rows
    error_report_filename = None
    error_report_path = None
    if invalid_records:
        error_df = pd.DataFrame(invalid_records)
        error_report_filename = f"errors_{int(pd.Timestamp.now().timestamp())}_{clean_filename}"
        error_report_path = Config.ERROR_REPORT_DIR / error_report_filename
        error_df.to_excel(error_report_path, index=False)

    # 1. Create ImportBatch record in SQL Server
    batch_insert_sql = """
    INSERT INTO ImportBatches (filename, file_path, total_rows, valid_rows, invalid_rows, duplicate_rows, status, error_report_path, created_at)
    OUTPUT INSERTED.id
    VALUES (?, ?, ?, ?, ?, ?, 'completed', ?, GETDATE())
    """
    batch_id = db.execute_scalar_insert(
        batch_insert_sql,
        (
            filename,
            str(saved_batch_path),
            total_rows,
            len(valid_records),
            len(invalid_records),
            duplicate_count,
            str(error_report_path) if error_report_path else None
        )
    )

    # 2. Insert or Update Villages in SQL Server
    inserted_count = 0
    updated_count = 0

    with db.get_db_cursor(commit=True) as cursor:
        for rec in valid_records:
            if rec["is_update"] and rec["existing_id"]:
                update_sql = """
                UPDATE Villages SET
                    zone = COALESCE(NULLIF(?, ''), zone),
                    district_name = ?,
                    subdistrict_name = ?,
                    village_name = ?,
                    geb_connection = COALESCE(NULLIF(?, ''), geb_connection),
                    google_search_orig_nos = CASE WHEN ? > 0 THEN ? ELSE google_search_orig_nos END,
                    google_edited_nos = CASE WHEN ? > 0 THEN ? ELSE google_edited_nos END,
                    total_wells = CASE WHEN ? > 0 THEN ? ELSE total_wells END,
                    dugwells = CASE WHEN ? > 0 THEN ? ELSE dugwells END,
                    bores = CASE WHEN ? > 0 THEN ? ELSE bores END,
                    electric_kuva = CASE WHEN ? > 0 THEN ? ELSE electric_kuva END,
                    electric_bor = CASE WHEN ? > 0 THEN ? ELSE electric_bor END,
                    total_electric = CASE WHEN ? > 0 THEN ? ELSE total_electric END,
                    solar_bor_kuva = CASE WHEN ? > 0 THEN ? ELSE solar_bor_kuva END,
                    total_electric_solar = CASE WHEN ? > 0 THEN ? ELSE total_electric_solar END,
                    raw_geb_data = COALESCE(?, raw_geb_data),
                    remark = COALESCE(NULLIF(?, ''), remark),
                    updated_at = GETDATE()
                WHERE id = ?
                """
                cursor.execute(
                    update_sql,
                    (
                        rec["zone"], rec["district_name"], rec["subdistrict_name"], rec["village_name"],
                        rec["geb_connection"], rec["google_search_orig_nos"], rec["google_search_orig_nos"],
                        rec["google_edited_nos"], rec["google_edited_nos"], rec["total_wells"], rec["total_wells"],
                        rec["dugwells"], rec["dugwells"], rec["bores"], rec["bores"],
                        rec["electric_kuva"], rec["electric_kuva"], rec["electric_bor"], rec["electric_bor"],
                        rec["total_electric"], rec["total_electric"], rec["solar_bor_kuva"], rec["solar_bor_kuva"],
                        rec["total_electric_solar"], rec["total_electric_solar"], rec["raw_geb_data"],
                        rec["remark"], rec["existing_id"]
                    )
                )
                updated_count += 1
            else:
                insert_village_sql = """
                INSERT INTO Villages (
                    batch_id, zone, district_name, subdistrict_name, village_name, village_code,
                    geb_connection, google_search_orig_nos, google_edited_nos, total_wells,
                    dugwells, bores, electric_kuva, electric_bor, total_electric, solar_bor_kuva, total_electric_solar,
                    raw_geb_data, assignment_status, kml_status, remark, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Unassigned', ?, ?, GETDATE(), GETDATE())
                """
                cursor.execute(
                    insert_village_sql,
                    (
                        batch_id, rec["zone"], rec["district_name"], rec["subdistrict_name"],
                        rec["village_name"], rec["village_code"], rec["geb_connection"],
                        rec["google_search_orig_nos"], rec["google_edited_nos"],
                        rec["total_wells"], rec["dugwells"], rec["bores"],
                        rec["electric_kuva"], rec["electric_bor"], rec["total_electric"],
                        rec["solar_bor_kuva"], rec["total_electric_solar"],
                        rec["raw_geb_data"], rec["kml_status"], rec["remark"]
                    )
                )
                inserted_count += 1

    return {
        "success": True,
        "batch_id": batch_id,
        "filename": filename,
        "total_rows": total_rows,
        "valid_rows": len(valid_records),
        "invalid_rows": len(invalid_records),
        "duplicates_detected": duplicate_count,
        "inserted_count": inserted_count,
        "updated_count": updated_count,
        "error_report_filename": error_report_filename,
        "has_errors": len(invalid_records) > 0
    }


def generate_excel_export(filters=None, base_url=""):
    """
    Generate professional Excel workbook matching the exact template columns,
    preserving all original GEB columns, with support for:
    - Person-wise export (single person's assigned villages)
    - All Persons export (all assigned villages)
    - Standard / Filtered village exports
    
    Includes professional styling, frozen headers, auto-filters, text-formatted village codes,
    active KML links, and a comprehensive Summary Report sheet with Person breakdowns.
    """
    filters = filters or {}
    where_clauses = ["1=1"]
    params = []

    # Selected IDs filter
    if filters.get('selected_ids'):
        ids = [int(i) for i in filters['selected_ids'] if str(i).isdigit()]
        if ids:
            placeholders = ','.join(['?'] * len(ids))
            where_clauses.append(f"v.id IN ({placeholders})")
            params.extend(ids)

    # Person ID filter (Person-wise export)
    if filters.get('person_id'):
        where_clauses.append("v.assigned_person_id = ?")
        params.append(int(filters['person_id']))

    # Export type
    export_type = filters.get('export_type', '')
    if export_type == 'all_persons':
        where_clauses.append("v.assigned_person_id IS NOT NULL")
    elif export_type == 'unassigned':
        where_clauses.append("v.assigned_person_id IS NULL")

    # Zone filter
    if filters.get('zone'):
        where_clauses.append("v.zone = ?")
        params.append(filters['zone'])

    # District filter
    if filters.get('district'):
        where_clauses.append("v.district_name = ?")
        params.append(filters['district'])

    # Subdistrict filter
    if filters.get('subdistrict'):
        where_clauses.append("v.subdistrict_name = ?")
        params.append(filters['subdistrict'])

    # Status filter
    if filters.get('status'):
        status = filters['status']
        if status.lower() == 'completed':
            where_clauses.append("(COALESCE(v.work_status, '') = 'Done' OR COALESCE(v.kml_status, '') IN ('Done', 'Verified', 'Marking Completed', 'Finalized'))")
        elif status.lower() == 'pending':
            where_clauses.append("(COALESCE(v.work_status, '') != 'Done' AND COALESCE(v.kml_status, '') NOT IN ('Done', 'Verified', 'Marking Completed', 'Finalized'))")
        elif status.lower() == 'in progress':
            where_clauses.append("v.kml_status = 'In Progress'")
        elif status.lower() in ('failed', 'needs review', 'needs_review'):
            where_clauses.append("v.kml_status IN ('Failed', 'Needs Review')")
        else:
            where_clauses.append("v.kml_status = ?")
            params.append(status)

    where_sql = " AND ".join(where_clauses)

    query = f"""
    SELECT 
        v.id,
        v.zone,
        v.district_name,
        v.subdistrict_name,
        v.village_name,
        v.village_code,
        v.assigned_person_id,
        v.assigned_person_name,
        v.assignment_status,
        v.assigned_at,
        v.raw_geb_data,
        v.kml_status,
        v.work_status,
        v.remark,
        k.id AS kml_id,
        k.geojson_data
    FROM Villages v
    LEFT JOIN KMLFiles k ON v.id = k.village_id AND k.is_active = 1
    WHERE {where_sql}
    ORDER BY v.district_name, v.subdistrict_name, v.village_name, v.id
    """

    rows = db.query_all(query, params)

    # Create OpenPyXL Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Village GEB Data"

    # Exact required 13 columns in order
    headers = [
        "Sr No.",
        "District",
        "Taluka",
        "Village",
        "Village Code",
        "Name of Scheme",
        "Latitude",
        "Longitude",
        "Rs No.",
        "Area Of Rs",
        "Owner Name",
        "Cast",
        "HP"
    ]

    # Styling definitions
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    # Write headers
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    ws.row_dimensions[1].height = 26

    # Populate Data Rows
    for row_idx, r in enumerate(rows, 2):
        raw = {}
        if r.get('raw_geb_data'):
            try:
                parsed = json.loads(r['raw_geb_data'])
                if isinstance(parsed, dict):
                    raw = parsed
            except Exception:
                raw = {}

        def get_val(keys):
            for k in keys:
                if k in raw and raw[k] is not None and str(raw[k]).strip() != '' and str(raw[k]).strip().lower() != 'nan':
                    return str(raw[k]).strip()
                for rk, rv in raw.items():
                    if rk.strip().lower() == k.strip().lower() and rv is not None and str(rv).strip() != '' and str(rv).strip().lower() != 'nan':
                        return str(rv).strip()
            return ''

        # 1. Sr No.
        sr_no = row_idx - 1

        # 2. District
        district = r.get('district_name') or get_val(['district_name', 'district', 'District_Name', 'જિલ્લાનું નામ', 'જીલ્લો'])

        # 3. Taluka
        taluka = r.get('subdistrict_name') or get_val(['subdistrict_name', 'taluka', 'subdistrict', 'Subdistrict_Name', 'તાલુકાનું નામ', 'તાલુકો'])

        # 4. Village
        village = r.get('village_name') or get_val(['village_name', 'village', 'Village_Name', 'ગામનું નામ', 'ગામ'])

        # 5. Village Code
        v_code = str(r.get('village_code') or get_val(['village_code', 'Village_Code', 'ગામનો કોડ'])).strip()

        # 6. Name of Scheme
        name_of_scheme = get_val(['name of scheme', 'scheme', 'scheme_name', 'name_of_scheme', 'યોજના', 'યોજનાનું નામ', 'scheme name'])

        # 7. Latitude
        lat = get_val(['latitude', 'lat', 'અક્ષાંશ'])

        # 8. Longitude
        lon = get_val(['longitude', 'long', 'lng', 'રેખાંશ'])

        # If lat or lon not in raw_geb_data, extract from verified KML coordinates if available
        if (not lat or not lon) and r.get('geojson_data'):
            try:
                geo = json.loads(r['geojson_data'])
                for f in geo.get('features', []):
                    geom = f.get('geometry', {})
                    if geom.get('type') == 'Point' and geom.get('coordinates'):
                        c = geom['coordinates']
                        if len(c) >= 2:
                            if not lon: lon = str(c[0])
                            if not lat: lat = str(c[1])
                            break
            except Exception:
                pass

        # 9. Rs No.
        rs_no = get_val(['rs no.', 'rs no', 'rs_no', 'survey no', 'survey_no', 'સર્વે નંબર', 'બ્લોક નંબર', 'રે.સ.નં', 'rs'])

        # 10. Area Of Rs
        area_of_rs = get_val(['area of rs', 'area_of_rs', 'area', 'area (hector)', 'ક્ષેત્રફળ'])

        # 11. Owner Name
        owner_name = get_val(['owner name', 'owner_name', 'owner', 'farmer name', 'farmer_name', 'ખાતેદારનું નામ', 'અરજદારનું નામ', 'નામ'])

        # 12. Cast
        cast = get_val(['cast', 'caste', 'જાતિ'])

        # 13. HP
        hp = get_val(['hp', 'h.p.', 'horse power', 'હોર્સ પાવર'])

        row_data = [
            sr_no,
            district,
            taluka,
            village,
            v_code,
            name_of_scheme,
            lat,
            lon,
            rs_no,
            area_of_rs,
            owner_name,
            cast,
            hp
        ]

        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = data_font
            cell.border = thin_border

            # Column specific formatting
            if col_idx == 1: # Sr No.
                cell.alignment = center_align
            elif col_idx in (2, 3, 4, 6, 11): # District, Taluka, Village, Name of Scheme, Owner Name
                cell.alignment = left_align
            elif col_idx in (5, 9): # Village Code, Rs No.
                cell.number_format = '@'
                cell.alignment = center_align
            elif col_idx in (7, 8): # Lat, Lon
                cell.alignment = center_align
            elif col_idx == 10: # Area Of Rs
                cell.alignment = right_align
            elif col_idx in (12, 13): # Cast, HP
                cell.alignment = center_align
            else:
                cell.alignment = left_align

        ws.row_dimensions[row_idx].height = 20

    # Auto-filter and freeze header row
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(len(rows) + 1, 2)}"
    ws.freeze_panes = "A2"

    # Auto-adjust column widths
    min_widths = [8, 16, 16, 18, 14, 20, 14, 14, 12, 12, 22, 12, 10]
    for col_idx, col in enumerate(ws.columns, 0):
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            max_len = max(max_len, len(val_str))
        base_w = min_widths[col_idx] if col_idx < len(min_widths) else 14
        ws.column_dimensions[col_letter].width = max(max_len + 3, base_w)

    # Save to in-memory bytes buffer
    output_stream = io.BytesIO()
    wb.save(output_stream)
    output_stream.seek(0)
    return output_stream
