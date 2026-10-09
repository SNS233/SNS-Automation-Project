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
        where_clauses.append("v.zone = ?")
        params.append(zone.strip())

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
        if status.lower() == 'completed':
            where_clauses.append("v.kml_status IN ('Done', 'Verified', 'Marking Completed', 'Finalized')")
        elif status.lower() == 'pending':
            where_clauses.append("v.kml_status IN ('Pending', 'Ready to Process')")
        elif status.lower() == 'in progress':
            where_clauses.append("v.kml_status = 'In Progress'")
        elif status.lower() in ('failed', 'needs review', 'needs_review'):
            where_clauses.append("v.kml_status IN ('Failed', 'Needs Review')")
        else:
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
            v.generated_review_url,
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
        # Build zone filter clause for summary KPIs if a specific zone is selected
        z_where = ""
        z_params = []
        if zone:
            if zone == 'Unassigned Zone':
                z_where = "WHERE (zone IS NULL OR TRIM(zone) = '')"
            else:
                z_where = "WHERE zone = ?"
                z_params = [zone]

        # 1. Total Villages & Assignment KPI counts (respecting active zone filter)
        total_sql = f"SELECT COUNT(*) AS c FROM Villages {z_where}"
        total_row = db.query_one(total_sql, z_params)
        total_villages = total_row['c'] if total_row else 0

        # Completed Villages: strictly checked by completion flag
        comp_cond = "(COALESCE(work_status, '') = 'Done' OR COALESCE(kml_status, '') IN ('Done', 'Verified', 'Marking Completed', 'Finalized'))"
        comp_where = f"WHERE {comp_cond}" if not z_where else f"{z_where} AND {comp_cond}"
        completed_row = db.query_one(f"SELECT COUNT(*) AS c FROM Villages {comp_where}", z_params)
        completed_villages = completed_row['c'] if completed_row else 0

        # Pending Villages (Not Done): Strictly Total - Completed
        pending_villages = max(0, total_villages - completed_villages)

        assign_where = "WHERE assigned_person_id IS NOT NULL" if not z_where else f"{z_where} AND assigned_person_id IS NOT NULL"
        assigned_row = db.query_one(f"SELECT COUNT(*) AS c FROM Villages {assign_where}", z_params)
        assigned_villages = assigned_row['c'] if assigned_row else 0

        unassign_where = "WHERE assigned_person_id IS NULL" if not z_where else f"{z_where} AND assigned_person_id IS NULL"
        unassigned_row = db.query_one(f"SELECT COUNT(*) AS c FROM Villages {unassign_where}", z_params)
        unassigned_villages = unassigned_row['c'] if unassigned_row else 0

        persons_row = db.query_one("SELECT COUNT(*) AS c FROM Persons WHERE is_active = 1")
        persons_count = persons_row['c'] if persons_row else 0

        # Status aggregates
        stats_sql = f"""
        SELECT 
            kml_status,
            COUNT(*) AS count,
            COALESCE(SUM(CAST(dugwells AS BIGINT)), 0) AS sum_dugwells,
            COALESCE(SUM(CAST(bores AS BIGINT)), 0) AS sum_bores,
            COALESCE(SUM(CAST(total_wells AS BIGINT)), 0) AS sum_total_wells
        FROM Villages
        {z_where}
        GROUP BY kml_status
        """
        stats = db.query_all(stats_sql, z_params)

        status_map = {r['kml_status']: r['count'] for r in stats}
        total_dugwells = sum(r['sum_dugwells'] for r in stats)
        total_bores = sum(r['sum_bores'] for r in stats)
        total_wells = sum(r['sum_total_wells'] for r in stats)

        in_progress = status_map.get('In Progress', 0)
        marking_completed = status_map.get('Marking Completed', 0)
        kml_downloaded = status_map.get('KML Downloaded', 0)
        failed_review = status_map.get('Failed', 0) + status_map.get('Needs Review', 0)

        # Active KML count
        kml_count_row = db.query_one("SELECT COUNT(*) AS c FROM KMLFiles WHERE is_active = 1")
        kml_count = kml_count_row['c'] if kml_count_row else 0

        # Progress percentage
        progress_pct = round((completed_villages / total_villages * 100), 1) if total_villages > 0 else 0.0

        # Recent villages (fast limited query for lightweight dashboard)
        recent_where = z_where.replace('zone', 'v.zone')
        recent_villages = db.query_all(f"""
        SELECT TOP 6 
            v.id, v.village_name, v.village_code, v.district_name, v.subdistrict_name, v.zone,
            v.kml_status, v.work_status, v.total_wells, v.bores, v.dugwells, v.updated_at,
            k.id AS kml_id
        FROM Villages v
        LEFT JOIN KMLFiles k ON v.id = k.village_id AND k.is_active = 1
        {recent_where}
        ORDER BY v.updated_at DESC
        """, z_params)

        # Fast filter options for UI
        districts = [r['district_name'] for r in db.query_all("SELECT DISTINCT district_name FROM Villages WHERE district_name IS NOT NULL ORDER BY district_name")]
        zones = [r['zone'] for r in db.query_all("SELECT DISTINCT zone FROM Villages WHERE zone IS NOT NULL AND zone <> '' ORDER BY zone")]

        # Zone-wise Insights & Progress breakdown (across all zones)
        zone_rows = db.query_all("""
        SELECT 
            COALESCE(NULLIF(TRIM(zone), ''), 'Unassigned Zone') AS zone_name,
            COUNT(*) AS total_villages,
            SUM(CASE WHEN (COALESCE(work_status, '') = 'Done' OR COALESCE(kml_status, '') IN ('Done', 'Verified', 'Marking Completed', 'Finalized')) THEN 1 ELSE 0 END) AS completed_villages,
            SUM(CASE WHEN kml_status = 'In Progress' AND COALESCE(work_status, '') != 'Done' THEN 1 ELSE 0 END) AS in_progress_villages,
            SUM(CASE WHEN (COALESCE(work_status, '') != 'Done' AND COALESCE(kml_status, '') NOT IN ('Done', 'Verified', 'Marking Completed', 'Finalized')) THEN 1 ELSE 0 END) AS pending_villages
        FROM Villages
        GROUP BY COALESCE(NULLIF(TRIM(zone), ''), 'Unassigned Zone')
        ORDER BY zone_name ASC
        """)

        zone_insights = []
        for r in zone_rows:
            tot = r['total_villages'] or 0
            comp = r['completed_villages'] or 0
            in_prog = r['in_progress_villages'] or 0
            pend = r['pending_villages'] or 0
            comp_pct = round((comp / tot * 100), 1) if tot > 0 else 0.0
            rem_pct = round(max(0.0, 100.0 - comp_pct), 1) if tot > 0 else 0.0

            zone_insights.append({
                "zone_name": r['zone_name'],
                "total_villages": tot,
                "completed_villages": comp,
                "pending_villages": pend,
                "in_progress_villages": in_prog,
                "completion_percentage": comp_pct,
                "remaining_percentage": rem_pct
            })

        # Calculate Executive 4 Zone Overview KPIs
        total_zones_count = len(zone_insights)
        completed_zones_count = sum(1 for z in zone_insights if z['completion_percentage'] == 100.0 and z['total_villages'] > 0)
        in_progress_zones_count = sum(1 for z in zone_insights if 0 < z['completion_percentage'] < 100.0)
        pending_zones_count = sum(1 for z in zone_insights if z['completion_percentage'] == 0.0)

        zone_kpis = {
            "total_zones": total_zones_count,
            "completed_zones": completed_zones_count,
            "in_progress_zones": in_progress_zones_count,
            "pending_zones": pending_zones_count
        }

        return {
            "summary": {
                "total_villages": total_villages,
                "pending_villages": pending_villages,
                "unassigned_villages": unassigned_villages,
                "assigned_villages": assigned_villages,
                "completed_villages": completed_villages,
                "persons_count": persons_count,
                "in_progress": in_progress,
                "marking_completed": marking_completed,
                "kml_downloaded": kml_downloaded,
                "failed_review": failed_review,
                "total_dugwells": total_dugwells,
                "total_bores": total_bores,
                "total_wells": total_wells,
                "kml_files_count": kml_count,
                "progress_percentage": progress_pct
            },
            "status_distribution": {
                "Pending": pending_villages,
                "In Progress": in_progress,
                "Marking Completed": marking_completed,
                "KML Downloaded": kml_downloaded,
                "Done / Verified": completed_villages,
                "Needs Review / Failed": failed_review
            },
            "district_breakdown": [],
            "zone_insights": zone_insights,
            "zone_kpis": zone_kpis,
            "selected_zone": zone,
            "recent_villages": recent_villages,
            "recent_imports": [],
            "recent_kmls": [],
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


