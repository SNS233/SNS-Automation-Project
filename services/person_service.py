import logging
import math
import db
from services.sync_service import bump_state_version

logger = logging.getLogger(__name__)


def list_persons():
    """
    Fetch all persons with their active status and count of assigned villages.
    """
    sql = """
    SELECT 
        p.id,
        p.name,
        p.email,
        p.phone,
        p.role,
        p.is_active,
        p.notes,
        p.created_at,
        p.updated_at,
        COUNT(v.id) AS assigned_count
    FROM Persons p
    LEFT JOIN Villages v ON p.id = v.assigned_person_id
    GROUP BY p.id, p.name, p.email, p.phone, p.role, p.is_active, p.notes, p.created_at, p.updated_at
    ORDER BY p.name ASC
    """
    rows = db.query_all(sql)
    return rows


def get_person_by_id(person_id):
    """
    Fetch details for a specific person along with the list of villages assigned to them.
    """
    person = db.query_one("SELECT * FROM Persons WHERE id = ?", (person_id,))
    if not person:
        return None

    # Fetch all assigned villages
    villages_sql = """
    SELECT 
        id,
        village_name,
        village_code,
        district_name,
        subdistrict_name,
        zone,
        total_wells,
        dugwells,
        bores,
        kml_status,
        assignment_status,
        assigned_at
    FROM Villages
    WHERE assigned_person_id = ?
    ORDER BY district_name ASC, subdistrict_name ASC, village_name ASC
    """
    assigned_villages = db.query_all(villages_sql, (person_id,))
    person['assigned_count'] = len(assigned_villages)
    person['assigned_villages'] = assigned_villages
    return person


def create_person(data):
    """
    Add a new person to the system.
    """
    name = str(data.get('name') or '').strip()
    if not name:
        raise ValueError("Person Name is required.")

    email = str(data.get('email') or '').strip() or None
    phone = str(data.get('phone') or '').strip() or None
    role = str(data.get('role') or 'Field Surveyor').strip()
    notes = str(data.get('notes') or '').strip() or None

    sql = """
    INSERT INTO Persons (name, email, phone, role, is_active, notes, created_at, updated_at)
    VALUES (?, ?, ?, ?, 1, ?, GETDATE(), GETDATE())
    """
    person_id = db.execute_scalar_insert(sql, (name, email, phone, role, notes))
    return get_person_by_id(person_id)


def update_person(person_id, data):
    """
    Update person information.
    """
    existing = db.query_one("SELECT * FROM Persons WHERE id = ?", (person_id,))
    if not existing:
        raise ValueError("Person not found.")

    name = str(data.get('name') or existing.get('name')).strip()
    if not name:
        raise ValueError("Person Name is required.")

    email = data.get('email', existing.get('email'))
    phone = data.get('phone', existing.get('phone'))
    role = data.get('role', existing.get('role'))
    notes = data.get('notes', existing.get('notes'))
    is_active = 1 if data.get('is_active', True) in (True, 1, '1', 'true') else 0

    sql = """
    UPDATE Persons SET
        name = ?,
        email = ?,
        phone = ?,
        role = ?,
        notes = ?,
        is_active = ?,
        updated_at = GETDATE()
    WHERE id = ?
    """
    db.execute_non_query(sql, (name, email, phone, role, notes, is_active, person_id))

    # Also synchronize assigned_person_name in Villages table
    db.execute_non_query(
        "UPDATE Villages SET assigned_person_name = ? WHERE assigned_person_id = ?",
        (name, person_id)
    )

    return get_person_by_id(person_id)


def delete_person(person_id):
    """
    Delete a person and automatically unassign their villages back to Pending status.
    """
    person = db.query_one("SELECT * FROM Persons WHERE id = ?", (person_id,))
    if not person:
        raise ValueError("Person not found.")

    # 1. Unassign all villages previously assigned to this person
    unassign_sql = """
    UPDATE Villages SET
        assigned_person_id = NULL,
        assigned_person_name = NULL,
        assigned_at = NULL,
        assignment_status = 'Unassigned'
    WHERE assigned_person_id = ?
    """
    unassigned_count = db.execute_non_query(unassign_sql, (person_id,))

    # 2. Mark active assignments as Closed
    db.execute_non_query(
        "UPDATE VillageAssignments SET status = 'Unassigned', unassigned_at = GETDATE() WHERE person_id = ? AND status = 'Active'",
        (person_id,)
    )

    # 3. Delete person record
    db.execute_non_query("DELETE FROM Persons WHERE id = ?", (person_id,))

    logger.info(f"Person '{person.get('name')}' (ID {person_id}) removed. {unassigned_count} villages unassigned.")
    return {
        "success": True,
        "deleted_person_id": person_id,
        "unassigned_villages_count": unassigned_count
    }


def assign_villages(village_ids, person_id, assigned_by='Admin'):
    """
    Assign one or multiple villages to a specific person.
    Decrements Pending KPI, increments Assigned KPI, and increments person's assigned count.
    """
    if not village_ids:
        raise ValueError("No villages selected for assignment.")

    person = db.query_one("SELECT * FROM Persons WHERE id = ?", (person_id,))
    if not person:
        raise ValueError("Target person does not exist.")

    clean_ids = [int(v) for v in village_ids if str(v).isdigit()]
    if not clean_ids:
        raise ValueError("Invalid village IDs provided.")

    assigned_count = 0
    person_name = person.get('name', 'Unknown')

    for vid in clean_ids:
        # Check current village assignment
        village = db.query_one("SELECT id, village_name, assigned_person_id FROM Villages WHERE id = ?", (vid,))
        if not village:
            continue

        # Update village record
        update_sql = """
        UPDATE Villages SET
            assigned_person_id = ?,
            assigned_person_name = ?,
            assigned_at = GETDATE(),
            assignment_status = 'Assigned'
        WHERE id = ?
        """
        db.execute_non_query(update_sql, (person_id, person_name, vid))

        # Log assignment record
        log_sql = """
        INSERT INTO VillageAssignments (village_id, person_id, assigned_by, assigned_at, status)
        VALUES (?, ?, ?, GETDATE(), 'Active')
        """
        try:
            db.execute_non_query(log_sql, (vid, person_id, assigned_by))
        except Exception:
            pass

        # Log in ProcessingHistory
        try:
            db.execute_non_query(
                "INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by, created_at) VALUES (?, ?, ?, ?, ?, GETDATE())",
                (vid, 'Pending', 'Assigned', f"Assigned to {person_name}", assigned_by)
            )
        except Exception:
            pass

        assigned_count += 1

    # Automatically trigger background generation for villages without genuine review URL
    try:
        from services.user_work_service import auto_generate_assigned_villages
        auto_generate_assigned_villages(clean_ids)
    except Exception as e:
        logger.debug(f"Auto-generate trigger notice: {e}")

    bump_state_version()
    return {
        "success": True,
        "assigned_count": assigned_count,
        "person_id": person_id,
        "person_name": person_name
    }


def unassign_villages(village_ids, changed_by='Admin'):
    """
    Remove assignment for one or multiple villages, returning them to Pending.
    Increments Pending KPI, decrements Assigned KPI.
    """
    if not village_ids:
        raise ValueError("No villages selected for unassignment.")

    clean_ids = [int(v) for v in village_ids if str(v).isdigit()]
    if not clean_ids:
        raise ValueError("Invalid village IDs provided.")

    unassigned_count = 0
    for vid in clean_ids:
        village = db.query_one("SELECT id, assigned_person_name FROM Villages WHERE id = ?", (vid,))
        if not village:
            continue

        prev_person = village.get('assigned_person_name') or 'Assigned Person'

        # Reset assignment on village
        update_sql = """
        UPDATE Villages SET
            assigned_person_id = NULL,
            assigned_person_name = NULL,
            assigned_at = NULL,
            assignment_status = 'Unassigned'
        WHERE id = ?
        """
        db.execute_non_query(update_sql, (vid,))

        # Update assignment history
        try:
            db.execute_non_query(
                "UPDATE VillageAssignments SET status = 'Unassigned', unassigned_at = GETDATE() WHERE village_id = ? AND status = 'Active'",
                (vid,)
            )
        except Exception:
            pass

        try:
            db.execute_non_query(
                "INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by, created_at) VALUES (?, ?, ?, ?, ?, GETDATE())",
                (vid, 'Assigned', 'Pending', f"Unassigned from {prev_person}", changed_by)
            )
        except Exception:
            pass

        unassigned_count += 1

    if unassigned_count > 0:
        bump_state_version()

    return {
        "success": True,
        "unassigned_count": unassigned_count
    }


def get_unassigned_villages(page=1, page_size=20, search='', district='', subdistrict='', zone=''):
    """
    Query unassigned (pending) villages available to be assigned to a person.
    """
    page = max(1, int(page))
    page_size = min(max(1, int(page_size)), 200)
    offset = (page - 1) * page_size

    where_clauses = ["v.assigned_person_id IS NULL"]
    params = []

    if search:
        s_pat = f"%{search.strip()}%"
        where_clauses.append("(v.village_name LIKE ? OR v.village_code LIKE ?)")
        params.extend([s_pat, s_pat])

    if zone:
        where_clauses.append("v.zone = ?")
        params.append(zone.strip())

    if district:
        where_clauses.append("v.district_name = ?")
        params.append(district.strip())

    if subdistrict:
        where_clauses.append("v.subdistrict_name = ?")
        params.append(subdistrict.strip())

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) AS total FROM Villages v WHERE {where_sql}"
    count_row = db.query_one(count_sql, params)
    total_count = count_row['total'] if count_row else 0
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    query_sql = f"""
    SELECT 
        v.id,
        v.village_name,
        v.village_code,
        v.district_name,
        v.subdistrict_name,
        v.zone,
        v.total_wells,
        v.dugwells,
        v.bores,
        v.kml_status,
        v.assignment_status,
        v.created_at
    FROM Villages v
    WHERE {where_sql}
    ORDER BY v.district_name ASC, v.subdistrict_name ASC, v.village_name ASC
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


def get_assigned_villages(person_id=None, page=1, page_size=20, search='', district='', subdistrict='', zone=''):
    """
    Query villages that are currently assigned (optionally filtered by person_id).
    """
    page = max(1, int(page))
    page_size = min(max(1, int(page_size)), 200)
    offset = (page - 1) * page_size

    where_clauses = ["v.assigned_person_id IS NOT NULL"]
    params = []

    if person_id:
        where_clauses.append("v.assigned_person_id = ?")
        params.append(int(person_id))

    if search:
        s_pat = f"%{search.strip()}%"
        where_clauses.append("(v.village_name LIKE ? OR v.village_code LIKE ? OR v.assigned_person_name LIKE ?)")
        params.extend([s_pat, s_pat, s_pat])

    if zone:
        where_clauses.append("v.zone = ?")
        params.append(zone.strip())

    if district:
        where_clauses.append("v.district_name = ?")
        params.append(district.strip())

    if subdistrict:
        where_clauses.append("v.subdistrict_name = ?")
        params.append(subdistrict.strip())

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) AS total FROM Villages v WHERE {where_sql}"
    count_row = db.query_one(count_sql, params)
    total_count = count_row['total'] if count_row else 0
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    query_sql = f"""
    SELECT 
        v.id,
        v.village_name,
        v.village_code,
        v.district_name,
        v.subdistrict_name,
        v.zone,
        v.total_wells,
        v.dugwells,
        v.bores,
        v.kml_status,
        COALESCE(v.work_status, 'Not Done') AS work_status,
        v.assigned_person_id,
        v.assigned_person_name,
        v.assigned_at,
        v.updated_at,
        v.assignment_status
    FROM Villages v
    WHERE {where_sql}
    ORDER BY v.assigned_at DESC, v.district_name ASC, v.village_name ASC
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
