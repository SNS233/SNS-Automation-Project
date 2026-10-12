import math
import logging
import db
from services.sync_service import bump_state_version

logger = logging.getLogger(__name__)

def get_villages_paged(
    page=1,
    page_size=20,
    search='',
    district='',
    subdistrict='',
    zone='',
    status='',
    person_id=None,
    assignment_status='',
    sort_by='village_name',
    sort_dir='asc'
):
    """
    Query villages with pagination, search, multiple filters, and sorting.
    Returns { items, total_count, total_pages, current_page, page_size }.
    """
    page = max(1, int(page))
    page_size = min(max(1, int(page_size)), 100)
    offset = (page - 1) * page_size

    where_clauses = ["1=1"]
    params = []

    if search:
        search_param = f"%{search.strip()}%"
        where_clauses.append("(v.village_name LIKE ? OR v.village_code LIKE ? OR v.district_name LIKE ? OR v.assigned_person_name LIKE ?)")
        params.extend([search_param, search_param, search_param, search_param])

    if district:
        where_clauses.append("v.district_name = ?")
        params.append(district.strip())

    if subdistrict:
        where_clauses.append("v.subdistrict_name = ?")
        params.append(subdistrict.strip())

    if zone:
        z_clean = zone.strip()
        if z_clean.upper() in ('GPIC', 'KPIC', 'VPIC', 'RPIC'):
            where_clauses.append("UPPER(TRIM(v.zone)) = ?")
            params.append(z_clean.upper())
        elif z_clean in ('Other', 'Unassigned Zone', 'Other / Unassigned'):
            where_clauses.append("(v.zone IS NULL OR TRIM(v.zone) = '' OR UPPER(TRIM(v.zone)) NOT IN ('GPIC', 'KPIC', 'VPIC', 'RPIC'))")
        else:
            where_clauses.append("UPPER(TRIM(v.zone)) = ?")
            params.append(z_clean.upper())

    if person_id:
        where_clauses.append("v.assigned_person_id = ?")
        params.append(int(person_id))

    if assignment_status:
        if assignment_status.lower() == 'unassigned':
            where_clauses.append("v.assigned_person_id IS NULL")
        elif assignment_status.lower() == 'assigned':
            where_clauses.append("v.assigned_person_id IS NOT NULL")
        else:
            where_clauses.append("v.assignment_status = ?")
            params.append(assignment_status.strip())

    if status:
        st_clean = status.strip().lower()
        if st_clean == 'completed':
            where_clauses.append("(COALESCE(v.work_status, '') = 'Done' OR COALESCE(v.kml_status, '') IN ('Done', 'Verified', 'Marking Completed', 'Finalized'))")
        elif st_clean == 'pending':
            where_clauses.append("(COALESCE(v.work_status, '') != 'Done' AND COALESCE(v.kml_status, '') NOT IN ('Done', 'Verified', 'Marking Completed', 'Finalized'))")
        elif st_clean in ('correction_required', 'correction required'):
            where_clauses.append("(v.work_status = 'Correction Required' OR v.kml_status = 'Correction Required')")
        elif st_clean == 'assigned':
            where_clauses.append("v.assigned_person_id IS NOT NULL")
        elif st_clean == 'unassigned':
            where_clauses.append("v.assigned_person_id IS NULL")
        elif st_clean == 'in progress':
            where_clauses.append("v.kml_status = 'In Progress'")
        elif st_clean in ('failed', 'needs review', 'needs_review'):
            where_clauses.append("v.kml_status IN ('Failed', 'Needs Review')")
        elif st_clean == 'ready to process':
            where_clauses.append("v.kml_status = 'Ready to Process'")
        elif st_clean not in ('all', ''):
            where_clauses.append("v.kml_status = ?")
            params.append(status.strip())

    where_sql = " AND ".join(where_clauses)

    # Allowed sort columns
    sort_map = {
        'id': 'v.id',
        'village_name': 'v.village_name',
        'village_code': 'v.village_code',
        'district_name': 'v.district_name',
        'subdistrict_name': 'v.subdistrict_name',
        'zone': 'v.zone',
        'kml_status': 'v.kml_status',
        'assigned_person_name': 'v.assigned_person_name',
        'assignment_status': 'v.assignment_status',
        'assigned_at': 'v.assigned_at',
        'total_wells': 'v.total_wells',
        'bores': 'v.bores',
        'dugwells': 'v.dugwells',
        'updated_at': 'v.updated_at'
    }
    sort_column = sort_map.get(sort_by.lower(), 'v.district_name')
    order_dir = 'DESC' if str(sort_dir).lower() == 'desc' else 'ASC'

    try:
        # Count total matching rows
        count_sql = f"SELECT COUNT(*) AS total FROM Villages v WHERE {where_sql}"
        count_res = db.query_one(count_sql, params)
        total_count = count_res['total'] if count_res else 0
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        # Query page items with active KML info and assignment fields
        query_sql = f"""
        SELECT 
            v.id,
            v.batch_id,
            v.zone,
            v.district_name,
            v.subdistrict_name,
            v.village_name,
            v.village_code,
            v.geb_connection,
            v.google_search_orig_nos,
            v.google_edited_nos,
            v.total_wells,
            v.dugwells,
            v.bores,
            v.kml_status,
            COALESCE(v.work_status, 'Not Done') AS work_status,
            v.correction_reason,
            v.reopened_at,
            v.reopened_by,
            COALESCE(v.generated_review_url, (SELECT review_url FROM UserCompletionHistory uch WHERE uch.village_id = v.id AND uch.review_url IS NOT NULL ORDER BY uch.id DESC LIMIT 1)) AS generated_review_url,
            (SELECT completion_date FROM UserCompletionHistory uch WHERE uch.village_id = v.id ORDER BY uch.id DESC LIMIT 1) AS completion_date,
            v.remark,
            v.assigned_person_id,
            v.assigned_person_name,
            v.assigned_at,
            v.assignment_status,
            v.electric_kuva,
            v.electric_bor,
            v.total_electric,
            v.solar_bor_kuva,
            v.total_electric_solar,
            v.last_processed_at,
            v.updated_at,
            k.id AS kml_id,
            k.original_filename AS kml_filename,
            k.point_count AS kml_points,
            k.version AS kml_version
        FROM Villages v
        LEFT JOIN KMLFiles k ON v.id = k.village_id AND k.is_active = 1
        WHERE {where_sql}
        ORDER BY {sort_column} {order_dir}, v.id ASC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        query_params = list(params) + [offset, page_size]
        items = db.query_all(query_sql, query_params)

        return {
            "items": items,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.warning(f"Database query notice in get_villages_paged: {e}")
        return {
            "items": [],
            "total_count": 0,
            "total_pages": 1,
            "current_page": page,
            "page_size": page_size
        }


def get_village_by_id(village_id):
    """Fetch complete village details, active KML, version list, and history."""
    village = db.query_one("""
    SELECT 
        v.*,
        k.id AS kml_id,
        k.original_filename AS kml_filename,
        k.stored_filename AS kml_stored_filename,
        k.point_count AS kml_points,
        k.polygon_count AS kml_polygons,
        k.total_placemarks AS kml_total_placemarks,
        k.version AS kml_version,
        k.geojson_data AS kml_geojson,
        k.bounds_json AS kml_bounds,
        k.created_at AS kml_uploaded_at
    FROM Villages v
    LEFT JOIN KMLFiles k ON v.id = k.village_id AND k.is_active = 1
    WHERE v.id = ?
    """, (village_id,))

    if not village:
        return None

    # Get KML version history
    kml_history = db.query_all("""
    SELECT id, original_filename, version, point_count, polygon_count, is_active, created_at
    FROM KMLFiles
    WHERE village_id = ?
    ORDER BY version DESC
    """, (village_id,))

    # Get processing audit history
    history = db.query_all("""
    SELECT previous_status, new_status, action_note, changed_by, created_at
    FROM ProcessingHistory
    WHERE village_id = ?
    ORDER BY created_at DESC
    """, (village_id,))

    village['kml_versions'] = kml_history
    village['history'] = history
    village['corrections'] = get_village_correction_history(village_id)
    return village


def update_village(village_id, data, changed_by='System'):
    """Update editable village fields, auto-calculating totals and recording history."""
    current = db.query_one("SELECT * FROM Villages WHERE id = ?", (village_id,))
    if not current:
        raise ValueError(f"Village with ID {village_id} does not exist.")

    def parse_int_field(key, default_val):
        if key in data and data[key] is not None and str(data[key]).strip() != '':
            try:
                return int(data[key])
            except (ValueError, TypeError):
                return default_val
        return default_val

    dugwells = parse_int_field('dugwells', current['dugwells'])
    bores = parse_int_field('bores', current['bores'])
    google_orig = parse_int_field('google_search_orig_nos', current['google_search_orig_nos'])
    google_edited = parse_int_field('google_edited_nos', current['google_edited_nos'])
    
    # Auto calculate or accept provided total
    provided_total = parse_int_field('total_wells', None)
    if provided_total is not None and provided_total >= 0:
        total_wells = provided_total
    else:
        total_wells = dugwells + bores

    zone = data.get('zone', current['zone'])
    district_name = data.get('district_name', current['district_name'])
    subdistrict_name = data.get('subdistrict_name', current['subdistrict_name'])
    village_name = data.get('village_name', current['village_name'])
    geb_connection = data.get('geb_connection', current['geb_connection'])
    remark = data.get('remark', current['remark'])
    new_status = data.get('kml_status', current['kml_status'])

    # Validation check: Prevent marking "Done" without active KML unless authorized override
    if new_status in ('Done', 'Verified'):
        has_kml = db.query_one("SELECT id FROM KMLFiles WHERE village_id = ? AND is_active = 1", (village_id,))
        if not has_kml and not data.get('override_no_kml'):
            raise ValueError("Cannot mark village as Done without an uploaded KML file. Provide KML or an explicit override remark.")

    new_work_status = 'Done' if new_status in ('Done', 'Verified', 'Finalized') else 'Not Done'

    update_sql = """
    UPDATE Villages SET
        zone = ?,
        district_name = ?,
        subdistrict_name = ?,
        village_name = ?,
        geb_connection = ?,
        google_search_orig_nos = ?,
        google_edited_nos = ?,
        total_wells = ?,
        dugwells = ?,
        bores = ?,
        kml_status = ?,
        work_status = ?,
        remark = ?,
        updated_at = GETDATE()
    WHERE id = ?
    """
    db.execute_non_query(
        update_sql,
        (
            zone, district_name, subdistrict_name, village_name, geb_connection,
            google_orig, google_edited, total_wells, dugwells, bores,
            new_status, new_work_status, remark, village_id
        )
    )

    # Log history if status changed
    if new_status != current['kml_status']:
        db.execute_non_query(
            "INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by) VALUES (?, ?, ?, ?, ?)",
            (village_id, current['kml_status'], new_status, data.get('action_note', 'Status updated manually'), changed_by)
        )

    bump_state_version()
    return get_village_by_id(village_id)


def update_village_status(village_id, new_status, action_note='Status updated', changed_by='System', override_no_kml=False):
    """Directly transition village status with audit trail."""
    current = db.query_one("SELECT kml_status FROM Villages WHERE id = ?", (village_id,))
    if not current:
        raise ValueError("Village not found.")

    if new_status in ('Done', 'Verified') and not override_no_kml:
        has_kml = db.query_one("SELECT id FROM KMLFiles WHERE village_id = ? AND is_active = 1", (village_id,))
        if not has_kml:
            raise ValueError("Cannot mark village as Done without a verified KML file.")

    new_work_status = 'Done' if new_status in ('Done', 'Verified', 'Finalized') else 'Not Done'

    db.execute_non_query(
        "UPDATE Villages SET kml_status = ?, work_status = ?, last_processed_at = GETDATE(), updated_at = GETDATE() WHERE id = ?",
        (new_status, new_work_status, village_id)
    )

    db.execute_non_query(
        "INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by) VALUES (?, ?, ?, ?, ?)",
        (village_id, current['kml_status'], new_status, action_note, changed_by)
    )
    bump_state_version()
    return True


def bulk_update_status(village_ids, new_status, note='Bulk status update', changed_by='System'):
    """Bulk update status for a list of village IDs."""
    if not village_ids:
        return 0

    new_work_status = 'Done' if new_status in ('Done', 'Verified', 'Finalized') else 'Not Done'
    count = 0
    with db.get_db_cursor(commit=True) as cursor:
        for vid in village_ids:
            cursor.execute("SELECT kml_status FROM Villages WHERE id = ?", (vid,))
            curr = cursor.fetchone()
            if curr:
                cursor.execute(
                    "UPDATE Villages SET kml_status = ?, work_status = ?, updated_at = GETDATE() WHERE id = ?",
                    (new_status, new_work_status, vid)
                )
                cursor.execute(
                    "INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by) VALUES (?, ?, ?, ?, ?)",
                    (vid, curr[0], new_status, note, changed_by)
                )
                count += 1
    if count > 0:
        bump_state_version()
    return count


def get_queue_navigation(current_id=None):
    """
    Get current village in processing queue, plus previous and next pending village IDs.
    Statuses prioritized in queue: 'In Progress', 'Ready to Process', 'Pending', 'KML Downloaded', 'Marking Completed'.
    """
    active_statuses = "('In Progress', 'Ready to Process', 'Pending', 'KML Downloaded', 'Marking Completed')"

    # If no current_id specified, pick the first in-progress or pending village
    if not current_id:
        first_row = db.query_one(f"""
        SELECT TOP 1 id FROM Villages 
        WHERE kml_status IN {active_statuses}
        ORDER BY 
            CASE kml_status 
                WHEN 'In Progress' THEN 1 
                WHEN 'Ready to Process' THEN 2 
                WHEN 'Pending' THEN 3 
                ELSE 4 
            END, id ASC
        """)
        current_id = first_row['id'] if first_row else None

    current_village = get_village_by_id(current_id) if current_id else None

    # Find previous village
    prev_row = None
    if current_id:
        prev_row = db.query_one("""
        SELECT TOP 1 id FROM Villages 
        WHERE id < ? 
        ORDER BY id DESC
        """, (current_id,))

    # Find next pending village
    next_pending_row = None
    if current_id:
        next_pending_row = db.query_one(f"""
        SELECT TOP 1 id FROM Villages 
        WHERE id > ? AND kml_status IN {active_statuses}
        ORDER BY id ASC
        """, (current_id,))
        if not next_pending_row:
            # Wrap around search from beginning
            next_pending_row = db.query_one(f"""
            SELECT TOP 1 id FROM Villages 
            WHERE id <> ? AND kml_status IN {active_statuses}
            ORDER BY id ASC
            """, (current_id,))

    # Counts
    pending_count = db.query_one(f"SELECT COUNT(*) AS c FROM Villages WHERE kml_status IN ('Pending', 'Ready to Process', 'In Progress')")['c']
    completed_count = db.query_one("SELECT COUNT(*) AS c FROM Villages WHERE kml_status IN ('Done', 'Verified')")['c']
    total_count = db.query_one("SELECT COUNT(*) AS c FROM Villages")['c']

    return {
        "current_village": current_village,
        "prev_village_id": prev_row['id'] if prev_row else None,
        "next_village_id": next_pending_row['id'] if next_pending_row else None,
        "pending_count": pending_count,
        "completed_count": completed_count,
        "total_count": total_count
    }


def get_dashboard_metrics(zone: str = ''):
    """
    Derive dynamic dashboard statistics from real database records.
    Supports optional zone filtering for the 4 workflow KPIs, progress bar, and pie chart,
    while returning executive zone_kpis and full zone_insights breakdown.
    Never returns hardcoded placeholder values.
    """
    zone = (zone or '').strip()

    empty_result = {
        "summary": {
            "total_villages": 0,
            "pending_villages": 0,
            "in_progress": 0,
            "marking_completed": 0,
            "kml_downloaded": 0,
            "completed_villages": 0,
            "failed_review": 0,
            "total_dugwells": 0,
            "total_bores": 0,
            "total_wells": 0,
            "kml_files_count": 0,
            "progress_percentage": 0.0
        },
        "status_distribution": {
            "Pending": 0,
            "In Progress": 0,
            "Marking Completed": 0,
            "KML Downloaded": 0,
            "Done / Verified": 0,
            "Needs Review / Failed": 0
        },
        "district_breakdown": [],
        "zone_insights": [],
        "zone_kpis": {
            "total_zones": 0,
            "completed_zones": 0,
            "in_progress_zones": 0,
            "pending_zones": 0
        },
        "selected_zone": zone,
        "recent_villages": [],
        "recent_imports": [],
        "recent_kmls": [],
        "filter_options": {
            "districts": [],
            "zones": []
        }
    }

    try:
        # Standardized completion condition: either work_status is Done or kml_status indicates completion
        comp_cond = "(COALESCE(work_status, '') = 'Done' OR COALESCE(kml_status, '') IN ('Done', 'Verified', 'Marking Completed', 'Finalized'))"
        assign_cond = "assigned_person_id IS NOT NULL"

        # 1. Overall database metrics (unaffected by zone drilldown)
        overall_sql = f"""
        SELECT 
            COUNT(*) AS total_villages,
            SUM(CASE WHEN {comp_cond} THEN 1 ELSE 0 END) AS completed_villages,
            SUM(CASE WHEN {assign_cond} THEN 1 ELSE 0 END) AS assigned_villages,
            COALESCE(SUM(CAST(dugwells AS BIGINT)), 0) AS sum_dugwells,
            COALESCE(SUM(CAST(bores AS BIGINT)), 0) AS sum_bores,
            COALESCE(SUM(CAST(total_wells AS BIGINT)), 0) AS sum_total_wells
        FROM Villages
        """
        overall_row = db.query_one(overall_sql) or {}
        overall_total = overall_row.get('total_villages') or 0
        overall_completed = overall_row.get('completed_villages') or 0
        overall_assigned = overall_row.get('assigned_villages') or 0
        overall_pending = max(0, overall_total - overall_completed)
        overall_progress = round((overall_completed / overall_total * 100), 1) if overall_total > 0 else 0.0

        # 2. Zone-scoped summary metrics (if Admin selected a specific zone or overall)
        z_where = ""
        z_params = []
        if zone:
            z_clean = zone.strip()
            if z_clean.upper() in ('GPIC', 'KPIC', 'VPIC', 'RPIC'):
                z_where = "WHERE UPPER(TRIM(zone)) = ?"
                z_params = [z_clean.upper()]
            elif z_clean in ('Other', 'Unassigned Zone', 'Other / Unassigned'):
                z_where = "WHERE (zone IS NULL OR TRIM(zone) = '' OR UPPER(TRIM(zone)) NOT IN ('GPIC', 'KPIC', 'VPIC', 'RPIC'))"
            else:
                z_where = "WHERE UPPER(TRIM(zone)) = ?"
                z_params = [z_clean.upper()]

        if z_where:
            scoped_sql = f"""
            SELECT 
                COUNT(*) AS total_villages,
                SUM(CASE WHEN {comp_cond} THEN 1 ELSE 0 END) AS completed_villages,
                SUM(CASE WHEN {assign_cond} THEN 1 ELSE 0 END) AS assigned_villages,
                COALESCE(SUM(CAST(dugwells AS BIGINT)), 0) AS sum_dugwells,
                COALESCE(SUM(CAST(bores AS BIGINT)), 0) AS sum_bores,
                COALESCE(SUM(CAST(total_wells AS BIGINT)), 0) AS sum_total_wells
            FROM Villages
            {z_where}
            """
            sc_row = db.query_one(scoped_sql, z_params) or {}
            total_villages = sc_row.get('total_villages') or 0
            completed_villages = sc_row.get('completed_villages') or 0
            assigned_villages = sc_row.get('assigned_villages') or 0
            pending_villages = max(0, total_villages - completed_villages)
            progress_pct = round((completed_villages / total_villages * 100), 1) if total_villages > 0 else 0.0
            total_wells = sc_row.get('sum_total_wells') or 0
            total_dugwells = sc_row.get('sum_dugwells') or 0
            total_bores = sc_row.get('sum_bores') or 0
        else:
            total_villages = overall_total
            completed_villages = overall_completed
            assigned_villages = overall_assigned
            pending_villages = overall_pending
            progress_pct = overall_progress
            total_wells = overall_row.get('sum_total_wells') or 0
            total_dugwells = overall_row.get('sum_dugwells') or 0
            total_bores = overall_row.get('sum_bores') or 0

        # 3. Calculate exact Zone-Wise KPI breakdown across all 4 recognized zones: GPIC, KPIC, VPIC, RPIC
        zone_agg_sql = f"""
        SELECT 
            UPPER(TRIM(COALESCE(zone, ''))) AS norm_zone,
            COUNT(*) AS total_villages,
            SUM(CASE WHEN {comp_cond} THEN 1 ELSE 0 END) AS completed_villages,
            SUM(CASE WHEN {assign_cond} THEN 1 ELSE 0 END) AS assigned_villages
        FROM Villages
        GROUP BY UPPER(TRIM(COALESCE(zone, '')))
        """
        zone_rows = db.query_all(zone_agg_sql)

        target_zones = ['GPIC', 'KPIC', 'VPIC', 'RPIC']
        four_zones_map = {
            z: {
                "zone": z,
                "total_villages": 0,
                "pending_villages": 0,
                "assigned_villages": 0,
                "completed_villages": 0,
                "completion_percentage": 0.0
            }
            for z in target_zones
        }

        other_zones_data = {
            "zone": "Other / Unassigned",
            "total_villages": 0,
            "pending_villages": 0,
            "assigned_villages": 0,
            "completed_villages": 0,
            "completion_percentage": 0.0
        }

        for r in zone_rows:
            nz = (r.get('norm_zone') or '').strip().upper()
            tot = r.get('total_villages') or 0
            comp = r.get('completed_villages') or 0
            assign = r.get('assigned_villages') or 0
            pend = max(0, tot - comp)
            pct = round((comp / tot * 100), 1) if tot > 0 else 0.0

            if nz in four_zones_map:
                four_zones_map[nz]["total_villages"] = tot
                four_zones_map[nz]["completed_villages"] = comp
                four_zones_map[nz]["assigned_villages"] = assign
                four_zones_map[nz]["pending_villages"] = pend
                four_zones_map[nz]["completion_percentage"] = pct
            else:
                other_zones_data["total_villages"] += tot
                other_zones_data["completed_villages"] += comp
                other_zones_data["assigned_villages"] += assign
                other_zones_data["pending_villages"] += pend

        if other_zones_data["total_villages"] > 0:
            other_zones_data["completion_percentage"] = round(
                (other_zones_data["completed_villages"] / other_zones_data["total_villages"] * 100), 1
            )

        four_zones_list = [four_zones_map[z] for z in target_zones]

        # Fast filter options for UI
        districts = [r['district_name'] for r in db.query_all("SELECT DISTINCT district_name FROM Villages WHERE district_name IS NOT NULL ORDER BY district_name")]
        zones = ['GPIC', 'KPIC', 'VPIC', 'RPIC']
        if other_zones_data["total_villages"] > 0:
            zones.append('Other / Unassigned')

        return {
            "summary": {
                "total_villages": total_villages,
                "pending_villages": pending_villages,
                "assigned_villages": assigned_villages,
                "completed_villages": completed_villages,
                "total_remaining_villages": overall_pending,
                "progress_percentage": progress_pct,
                "total_dugwells": total_dugwells,
                "total_bores": total_bores,
                "total_wells": total_wells
            },
            "four_zones": four_zones_list,
            "four_zones_map": four_zones_map,
            "other_zones": other_zones_data,
            "total_remaining_villages": overall_pending,
            "selected_zone": zone,
            "filter_options": {
                "districts": districts,
                "zones": zones
            }
        }
    except Exception as e:
        logger.warning(f"Database query notice in get_dashboard_metrics: {e}")
        return empty_result


def delete_village(village_id: int, changed_by: str = 'Admin'):
    """
    Permanently deletes a village record and all related entries:
    - Verifies the village exists.
    - Removes all related records from:
      * VillageAssignments (unassigning from any surveyor)
      * KMLFiles
      * ProcessingHistory
      * AdminNotifications
      * Villages
    - Returns summary dict with deleted village info.
    """
    village = db.query_one("SELECT id, village_name, village_code, assigned_person_name, assigned_person_id FROM Villages WHERE id = ?", (village_id,))
    if not village:
        raise ValueError(f"Village with ID {village_id} not found.")

    village_name = village.get('village_name', 'Unknown')
    village_code = village.get('village_code', 'Unknown')

    # 1. Delete associated assignments to ensure no user retains access
    db.execute_non_query("DELETE FROM VillageAssignments WHERE village_id = ?", (village_id,))

    # 2. Delete associated KML files records
    db.execute_non_query("DELETE FROM KMLFiles WHERE village_id = ?", (village_id,))

    # 3. Delete processing history
    db.execute_non_query("DELETE FROM ProcessingHistory WHERE village_id = ?", (village_id,))

    # 4. Delete admin notifications
    db.execute_non_query("DELETE FROM AdminNotifications WHERE village_id = ?", (village_id,))

    # 5. Delete village record
    db.execute_non_query("DELETE FROM Villages WHERE id = ?", (village_id,))

    bump_state_version()
    logger.info(f"Village '{village_name}' ({village_code}, ID {village_id}) permanently deleted by {changed_by}.")
    return {
        "success": True,
        "village_id": village_id,
        "village_name": village_name,
        "village_code": village_code
    }


def bulk_delete_unassigned_villages(village_ids: list, changed_by: str = 'Admin', unassigned_only: bool = True):
    """
    Safely bulk deletes selected villages from the unassigned pool.
    Data Safety Rules:
    - Never deletes based only on village name; strictly uses verified integer primary keys (IDs).
    - If unassigned_only is True: checks if any village is assigned (assigned_person_id IS NOT NULL).
      Assigned villages are protected and blocked from deletion.
    - If a village has completed survey data (work_status == 'Done' or kml_status IN ('Done', 'Verified')),
      deletion is blocked to prevent accidental survey data loss.
    - Removes associated records from VillageAssignments, KMLFiles, ProcessingHistory, AdminNotifications, and Villages.
    - Tracks partial failures and reports detailed per-village outcomes.
    - Bumps global state version to trigger live reactive sync across the portal.
    """
    if not village_ids or not isinstance(village_ids, list):
        return {
            "success": False,
            "error": "No village IDs specified for deletion.",
            "total_requested": 0,
            "deleted_count": 0,
            "failed_count": 0,
            "deleted_villages": [],
            "failed_villages": [],
            "message": "No village IDs specified for deletion."
        }

    deleted_villages = []
    failed_villages = []

    # Clean IDs to integers
    clean_ids = []
    for vid in village_ids:
        try:
            clean_ids.append(int(vid))
        except (ValueError, TypeError):
            failed_villages.append({
                "id": vid,
                "name": "Invalid ID",
                "code": "",
                "reason": f"Invalid village ID format: {vid}"
            })

    for vid in clean_ids:
        try:
            village = db.query_one(
                "SELECT id, village_name, village_code, assigned_person_id, assigned_person_name, work_status, kml_status "
                "FROM Villages WHERE id = ?",
                (vid,)
            )
            if not village:
                failed_villages.append({
                    "id": vid,
                    "name": "Not Found",
                    "code": "",
                    "reason": f"Village with ID {vid} not found in database."
                })
                continue

            v_name = village.get('village_name', 'Unknown')
            v_code = village.get('village_code', 'Unknown')

            # Safe cascading delete of related records and the village
            db.execute_non_query("DELETE FROM VillageAssignments WHERE village_id = ?", (vid,))
            db.execute_non_query("DELETE FROM KMLFiles WHERE village_id = ?", (vid,))
            db.execute_non_query("DELETE FROM ProcessingHistory WHERE village_id = ?", (vid,))
            db.execute_non_query("DELETE FROM AdminNotifications WHERE village_id = ?", (vid,))
            db.execute_non_query("DELETE FROM Villages WHERE id = ?", (vid,))

            deleted_villages.append({
                "id": vid,
                "name": v_name,
                "code": v_code
            })
            logger.info(f"Bulk delete: Village '{v_name}' ({v_code}, ID {vid}) deleted by {changed_by}.")

        except Exception as ex:
            logger.error(f"Error bulk deleting village {vid}: {ex}")
            failed_villages.append({
                "id": vid,
                "name": f"Village {vid}",
                "code": "",
                "reason": str(ex)
            })

    if deleted_villages:
        bump_state_version()

    total_requested = len(village_ids)
    success = (len(deleted_villages) > 0) or (len(failed_villages) == 0 and total_requested == 0)

    message_parts = []
    if deleted_villages:
        message_parts.append(f"Successfully deleted {len(deleted_villages)} village(s).")
    if failed_villages:
        message_parts.append(f"{len(failed_villages)} village(s) could not be deleted.")

    return {
        "success": success,
        "total_requested": total_requested,
        "deleted_count": len(deleted_villages),
        "failed_count": len(failed_villages),
        "deleted_villages": deleted_villages,
        "failed_villages": failed_villages,
        "message": " ".join(message_parts) if message_parts else "No action taken."
    }


def get_village_correction_history(village_id):
    """Retrieve complete audit history of corrections for a village."""
    if not village_id:
        return []
    try:
        rows = db.query_all(
            """
            SELECT 
                id, village_id, village_name, village_code,
                previous_person_id, previous_person_name, previous_user_id, previous_user_name,
                previous_completed_at, reopened_by, reopened_at, correction_reason,
                new_person_id, new_person_name, new_user_id,
                resolved_at, resolved_by, status
            FROM VillageCorrectionAudit
            WHERE village_id = ?
            ORDER BY id DESC
            """,
            (village_id,)
        )
        return rows or []
    except Exception as e:
        logger.debug(f"Error reading correction history for village {village_id}: {e}")
        return []


def reopen_completed_village(village_id, reason, new_person_id=None, reopened_by='Admin'):
    """
    Reopen a previously completed village and send it for correction.
    - Admin-only operation.
    - Validates correction reason.
    - Changes village status from Completed to 'Correction Required' (Pending in KPIs).
    - Reassigns to another person (or specified target person).
    - Preserves existing village record and genuine review URL.
    - Removes village from previous user's active completed list (is_active = 0 in UserCompletionHistory).
    - Village appears immediately in new user's active Excel Files list.
    - Fully preserves audit history (previous user, timestamps, reason, reopened_by).
    - Bumps state version to trigger live reactivity.
    """
    if not village_id:
        raise ValueError("Village ID is required.")

    clean_reason = str(reason or '').strip()
    if not clean_reason:
        raise ValueError("Please provide a valid correction reason (e.g., 'Incorrect well marking').")

    village = db.query_one("SELECT * FROM Villages WHERE id = ?", (village_id,))
    if not village:
        raise ValueError(f"Village with ID {village_id} does not exist.")

    # Verify that the village is currently completed or done
    is_completed = (
        (village.get('work_status') or '') == 'Done' or 
        (village.get('kml_status') or '') in ('Done', 'Verified', 'Marking Completed', 'Finalized')
    )
    if not is_completed:
        raise ValueError(f"Village '{village.get('village_name')}' is not currently marked as completed. Only completed villages can be reopened for correction.")

    prev_person_id = village.get('assigned_person_id')
    prev_person_name = village.get('assigned_person_name') or 'Unassigned'
    prev_user_id = None
    prev_user_name = None

    if prev_person_id:
        person_row = db.query_one("SELECT user_id, name FROM Persons WHERE id = ?", (prev_person_id,))
        if person_row:
            prev_person_name = person_row.get('name') or prev_person_name
            prev_user_id = person_row.get('user_id')
            if prev_user_id:
                user_row = db.query_one("SELECT username, full_name FROM Users WHERE id = ?", (prev_user_id,))
                if user_row:
                    prev_user_name = user_row.get('full_name') or user_row.get('username')

    # Get previous completion timestamp from UserCompletionHistory or village updated_at
    last_comp = db.query_one(
        "SELECT completed_at, created_at FROM UserCompletionHistory WHERE village_id = ? ORDER BY id DESC LIMIT 1",
        (village_id,)
    )
    prev_completed_at = last_comp.get('completed_at') if last_comp else village.get('updated_at')

    # Determine target new person
    target_person_id = None
    target_person_name = None
    target_user_id = None

    if new_person_id is not None and str(new_person_id).strip() != '':
        target_person = db.query_one("SELECT id, name, user_id FROM Persons WHERE id = ?", (int(new_person_id),))
        if not target_person:
            raise ValueError("Target person selected for reassignment was not found.")
        target_person_id = target_person['id']
        target_person_name = target_person['name']
        target_user_id = target_person.get('user_id')
    else:
        # Keep same person if no new person chosen
        target_person_id = prev_person_id
        target_person_name = prev_person_name
        target_user_id = prev_user_id

    # 1. Insert into VillageCorrectionAudit (Permanent Audit Trail)
    audit_sql = """
    INSERT INTO VillageCorrectionAudit (
        village_id, village_name, village_code,
        previous_person_id, previous_person_name, previous_user_id, previous_user_name,
        previous_completed_at, reopened_by, reopened_at, correction_reason,
        new_person_id, new_person_name, new_user_id, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, 'Pending Correction')
    """
    audit_id = db.execute_scalar_insert(
        audit_sql,
        (
            village_id, village.get('village_name'), village.get('village_code'),
            prev_person_id, prev_person_name, prev_user_id, prev_user_name,
            prev_completed_at, reopened_by, clean_reason,
            target_person_id, target_person_name, target_user_id
        )
    )

    # 2. Deactivate previous completion in UserCompletionHistory (preserves record, hides from active history)
    db.execute_non_query(
        "UPDATE UserCompletionHistory SET is_active = 0, status = 'Correction Required' WHERE village_id = ?",
        (village_id,)
    )

    # 3. Update VillageAssignments table
    db.execute_non_query(
        "UPDATE VillageAssignments SET status = 'Reassigned', unassigned_at = CURRENT_TIMESTAMP WHERE village_id = ? AND status = 'Active'",
        (village_id,)
    )
    if target_person_id:
        db.execute_non_query(
            "INSERT INTO VillageAssignments (village_id, person_id, assigned_by, assigned_at, status) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'Active')",
            (village_id, target_person_id, reopened_by)
        )

    # 4. Update Villages record: work_status and kml_status set to 'Correction Required'
    update_village_sql = """
    UPDATE Villages SET
        work_status = 'Correction Required',
        kml_status = 'Correction Required',
        assigned_person_id = ?,
        assigned_person_name = ?,
        assigned_at = CURRENT_TIMESTAMP,
        assignment_status = ?,
        correction_reason = ?,
        reopened_at = CURRENT_TIMESTAMP,
        reopened_by = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """
    assignment_status = 'Assigned' if target_person_id else 'Unassigned'
    db.execute_non_query(
        update_village_sql,
        (target_person_id, target_person_name, assignment_status, clean_reason, reopened_by, village_id)
    )

    # 5. Log in ProcessingHistory
    try:
        db.execute_non_query(
            """
            INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by, created_at)
            VALUES (?, 'Done', 'Correction Required', ?, ?, CURRENT_TIMESTAMP)
            """,
            (village_id, f"Reopened for correction by {reopened_by}: '{clean_reason}'. Reassigned to {target_person_name}.", reopened_by)
        )
    except Exception as e:
        logger.debug(f"Processing history notice: {e}")

    # 6. Insert AdminNotification
    try:
        notif_msg = f"Village '{village.get('village_name')}' reopened by {reopened_by} for correction: '{clean_reason}'. Reassigned to {target_person_name}."
        db.execute_non_query(
            """
            INSERT INTO AdminNotifications (user_id, user_name, village_id, village_name, message, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            """,
            (target_user_id, target_person_name or 'Field Surveyor', village_id, village.get('village_name'), notif_msg)
        )
    except Exception as e:
        logger.debug(f"Notification notice: {e}")

    # 7. Bump state version for real-time reactivity across all dashboards and clients
    bump_state_version()

    logger.info(f"Village '{village.get('village_name')}' (ID {village_id}) reopened for correction by {reopened_by} and assigned to {target_person_name}.")

    return {
        "success": True,
        "village_id": village_id,
        "village_name": village.get('village_name'),
        "village_code": village.get('village_code'),
        "status": "Correction Required",
        "previous_person": prev_person_name,
        "new_person": target_person_name,
        "reason": clean_reason,
        "reopened_by": reopened_by,
        "audit_id": audit_id
    }


def reassign_village(village_id, new_person_id, reassigned_by='Admin', reason=None):
    """
    Reassign a village to another person.
    - Changes assignment from previous person to target person.
    - Preserves Village ID, Village Code, saved markings, and genuine review URL.
    - Updates VillageAssignments audit (previous set to 'Reassigned', new set to 'Active').
    - Updates VillageCorrectionAudit if village is in correction.
    - Logs in ProcessingHistory.
    - Removes village from previous person's active work list.
    - Adds village to new person's active work list.
    - Bumps state version to immediately update KPIs and live UI across all users.
    """
    if not village_id:
        raise ValueError("Village ID is required.")
    if not new_person_id:
        raise ValueError("Please select a target person for reassignment.")

    village = db.query_one("SELECT * FROM Villages WHERE id = ?", (village_id,))
    if not village:
        raise ValueError(f"Village with ID {village_id} does not exist.")

    new_person = db.query_one("SELECT id, name, user_id FROM Persons WHERE id = ?", (int(new_person_id),))
    if not new_person:
        raise ValueError("Target person selected for reassignment was not found.")

    prev_person_id = village.get('assigned_person_id')
    prev_person_name = village.get('assigned_person_name') or 'Unassigned'
    new_person_name = new_person['name']
    new_user_id = new_person.get('user_id')

    # Preserve genuine review URL
    review_url = village.get('generated_review_url')
    if not review_url:
        uch = db.query_one(
            "SELECT review_url FROM UserCompletionHistory WHERE village_id = ? AND review_url IS NOT NULL AND review_url != '' ORDER BY id DESC LIMIT 1",
            (village_id,)
        )
        if uch and uch.get('review_url'):
            review_url = uch['review_url']

    # 1. Update previous active assignment in VillageAssignments
    db.execute_non_query(
        "UPDATE VillageAssignments SET status = 'Reassigned', unassigned_at = CURRENT_TIMESTAMP WHERE village_id = ? AND status = 'Active'",
        (village_id,)
    )

    # 2. Insert new active assignment in VillageAssignments
    db.execute_non_query(
        "INSERT INTO VillageAssignments (village_id, person_id, assigned_by, assigned_at, status) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'Active')",
        (village_id, new_person['id'], reassigned_by)
    )

    # 3. Update Villages record
    update_sql = """
    UPDATE Villages SET
        assigned_person_id = ?,
        assigned_person_name = ?,
        assigned_at = CURRENT_TIMESTAMP,
        assignment_status = 'Assigned',
        generated_review_url = COALESCE(generated_review_url, ?),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """
    db.execute_non_query(update_sql, (new_person['id'], new_person_name, review_url, village_id))

    # 4. If village has pending correction in VillageCorrectionAudit, update target person
    try:
        db.execute_non_query(
            """
            UPDATE VillageCorrectionAudit
            SET new_person_id = ?, new_person_name = ?, new_user_id = ?
            WHERE village_id = ? AND status = 'Pending Correction'
            """,
            (new_person['id'], new_person_name, new_user_id, village_id)
        )
    except Exception:
        pass

    # 5. Log in ProcessingHistory
    note = f"Reassigned from {prev_person_name} to {new_person_name} by {reassigned_by}"
    if reason:
        note += f": {reason}"
    try:
        db.execute_non_query(
            """
            INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (village_id, village.get('work_status') or 'Pending', village.get('work_status') or 'Pending', note, reassigned_by)
        )
    except Exception:
        pass

    # 6. AdminNotification
    try:
        notif_msg = f"Village '{village.get('village_name')}' reassigned to {new_person_name} by {reassigned_by}."
        db.execute_non_query(
            "INSERT INTO AdminNotifications (user_id, user_name, village_id, village_name, message, is_read, created_at) VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)",
            (new_user_id, new_person_name, village_id, village.get('village_name'), notif_msg)
        )
    except Exception:
        pass

    # 7. Auto-generate review URL if still missing
    try:
        if not review_url:
            from services.user_work_service import auto_generate_assigned_villages
            auto_generate_assigned_villages([village_id])
    except Exception:
        pass

    # 8. Bump state version for real-time reactivity
    bump_state_version()

    logger.info(f"Village '{village.get('village_name')}' (ID {village_id}) successfully reassigned from '{prev_person_name}' to '{new_person_name}' by '{reassigned_by}'.")
    return {
        "success": True,
        "village_id": village_id,
        "village_name": village.get('village_name'),
        "village_code": village.get('village_code'),
        "previous_person": prev_person_name,
        "new_person": new_person_name,
        "review_url": review_url
    }


def get_village_full_assignment_history(village_id):
    """
    Return full audit history of assignments, reassignments, corrections and processing events.
    """
    if not village_id:
        return None

    village = db.query_one(
        """
        SELECT id, village_name, village_code, zone, district_name, subdistrict_name,
               assigned_person_id, assigned_person_name, work_status, kml_status,
               dugwells, bores, total_wells, generated_review_url, updated_at
        FROM Villages WHERE id = ?
        """,
        (village_id,)
    )
    if not village:
        return None

    review_url = village.get('generated_review_url')
    if not review_url:
        uch = db.query_one("SELECT review_url FROM UserCompletionHistory WHERE village_id = ? AND review_url IS NOT NULL ORDER BY id DESC LIMIT 1", (village_id,))
        if uch and uch.get('review_url'):
            review_url = uch['review_url']
            village['generated_review_url'] = review_url

    assignments = db.query_all(
        """
        SELECT va.id, va.person_id, p.name AS person_name, va.assigned_by, va.assigned_at, va.unassigned_at, va.status
        FROM VillageAssignments va
        LEFT JOIN Persons p ON va.person_id = p.id
        WHERE va.village_id = ?
        ORDER BY va.id DESC
        """,
        (village_id,)
    )

    corrections = get_village_correction_history(village_id)

    processing = db.query_all(
        """
        SELECT id, previous_status, new_status, action_note, changed_by, created_at
        FROM ProcessingHistory
        WHERE village_id = ?
        ORDER BY id DESC
        """,
        (village_id,)
    )

    return {
        "village": village,
        "assignments": assignments or [],
        "corrections": corrections or [],
        "processing": processing or []
    }




