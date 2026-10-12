import logging
from werkzeug.security import generate_password_hash
import db

logger = logging.getLogger(__name__)


def list_users():
    """
    List all portal users along with their linked Person record,
    active status, and assigned village counts.
    """
    sql = """
    SELECT 
        u.id,
        u.username,
        u.full_name,
        u.role,
        u.is_active,
        u.created_at,
        p.id AS person_id,
        COALESCE(p.name, u.full_name, u.username) AS person_name,
        COUNT(CASE WHEN v.assigned_person_id = p.id AND (v.work_status != 'Done' AND v.kml_status != 'Done') THEN 1 END) AS pending_work_count,
        COUNT(CASE WHEN v.assigned_person_id = p.id AND (v.work_status = 'Done' OR v.kml_status = 'Done') THEN 1 END) AS completed_work_count,
        COUNT(v.id) AS total_assigned_count
    FROM Users u
    LEFT JOIN Persons p ON (p.user_id = u.id OR (p.user_id IS NULL AND LOWER(p.name) = LOWER(COALESCE(u.full_name, u.username))))
    LEFT JOIN Villages v ON v.assigned_person_id = p.id
    GROUP BY u.id, u.username, u.full_name, u.role, u.is_active, u.created_at, p.id, p.name
    ORDER BY u.id ASC
    """
    users = db.query_all(sql)
    return users


def get_user_by_id(user_id):
    """
    Get detailed information for a specific user.
    """
    user = db.query_one("SELECT id, username, full_name, role, is_active, created_at FROM Users WHERE id = ?", (user_id,))
    if not user:
        return None

    # Find linked person
    person = db.query_one(
        "SELECT id, name, email, phone, role, is_active FROM Persons WHERE user_id = ? OR LOWER(name) = LOWER(?)",
        (user_id, user.get('full_name') or user.get('username'))
    )
    user['person'] = person
    if person:
        user['person_id'] = person['id']
        assigned_villages = db.query_all(
            "SELECT id, village_name, village_code, district_name, subdistrict_name, kml_status, work_status, generated_review_url FROM Villages WHERE assigned_person_id = ?",
            (person['id'],)
        )
        user['assigned_villages'] = assigned_villages
        user['assigned_count'] = len(assigned_villages)
    else:
        user['person_id'] = None
        user['assigned_villages'] = []
        user['assigned_count'] = 0

    return user


def create_user(data):
    """
    Create a new portal user and automatically synchronize with the Assign Person system.
    """
    username = str(data.get('username') or '').strip()
    password = str(data.get('password') or '').strip()
    full_name = str(data.get('full_name') or '').strip() or username
    role = str(data.get('role') or 'user').strip().lower()
    is_active = 1 if data.get('is_active', True) in (True, 1, '1', 'true') else 0

    if not username:
        raise ValueError("Username is required.")
    if not password:
        raise ValueError("Password is required.")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters long.")

    # Check for existing username
    existing = db.query_one("SELECT id FROM Users WHERE LOWER(username) = LOWER(?)", (username,))
    if existing:
        raise ValueError(f"Username '{username}' already exists. Please choose a different username.")

    password_hash = generate_password_hash(password)

    user_sql = """
    INSERT INTO Users (username, password_hash, full_name, role, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, GETDATE())
    """
    user_id = db.execute_scalar_insert(user_sql, (username, password_hash, full_name, role, is_active))

    # Automatically add or link user to the Assign Person system
    existing_person = db.query_one(
        "SELECT id FROM Persons WHERE LOWER(name) = LOWER(?) OR user_id = ?",
        (full_name, user_id)
    )

    if existing_person:
        db.execute_non_query(
            "UPDATE Persons SET user_id = ?, is_active = ?, name = ?, updated_at = GETDATE() WHERE id = ?",
            (user_id, is_active, full_name, existing_person['id'])
        )
        person_id = existing_person['id']
    else:
        person_sql = """
        INSERT INTO Persons (name, email, phone, role, is_active, user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """
        person_id = db.execute_scalar_insert(
            person_sql,
            (full_name, f"{username}@portal.local", None, 'Field Surveyor', is_active, user_id)
        )

    logger.info(f"Created user '{username}' (ID {user_id}) and linked to Person ID {person_id}.")
    return get_user_by_id(user_id)


def update_user(user_id, data):
    """
    Update user credentials and profile details, syncing Persons table.
    """
    user = db.query_one("SELECT * FROM Users WHERE id = ?", (user_id,))
    if not user:
        raise ValueError("User not found.")

    username = str(data.get('username') or user.get('username')).strip()
    full_name = str(data.get('full_name') or user.get('full_name') or username).strip()
    role = str(data.get('role') or user.get('role', 'user')).strip().lower()
    is_active = 1 if data.get('is_active', user.get('is_active', 1)) in (True, 1, '1', 'true') else 0
    password = str(data.get('password') or '').strip()

    if not username:
        raise ValueError("Username is required.")

    # Check username uniqueness if changed
    dup = db.query_one("SELECT id FROM Users WHERE LOWER(username) = LOWER(?) AND id != ?", (username, user_id))
    if dup:
        raise ValueError(f"Username '{username}' is already in use by another account.")

    if password:
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters long.")
        pw_hash = generate_password_hash(password)
        db.execute_non_query(
            "UPDATE Users SET username = ?, password_hash = ?, full_name = ?, role = ?, is_active = ? WHERE id = ?",
            (username, pw_hash, full_name, role, is_active, user_id)
        )
    else:
        db.execute_non_query(
            "UPDATE Users SET username = ?, full_name = ?, role = ?, is_active = ? WHERE id = ?",
            (username, full_name, role, is_active, user_id)
        )

    # Sync Person table
    existing_person = db.query_one("SELECT id FROM Persons WHERE user_id = ?", (user_id,))
    if existing_person:
        db.execute_non_query(
            "UPDATE Persons SET name = ?, is_active = ?, updated_at = GETDATE() WHERE id = ?",
            (full_name, is_active, existing_person['id'])
        )
        # Also sync assigned_person_name in Villages table
        db.execute_non_query(
            "UPDATE Villages SET assigned_person_name = ? WHERE assigned_person_id = ?",
            (full_name, existing_person['id'])
        )
    else:
        # Create person if missing
        db.execute_non_query(
            "INSERT INTO Persons (name, email, phone, role, is_active, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())",
            (full_name, f"{username}@portal.local", None, 'Field Surveyor', is_active, user_id)
        )

    logger.info(f"Updated user ID {user_id} ('{username}').")
    return get_user_by_id(user_id)


def delete_user(user_id):
    """
    Delete user and unassign any villages assigned to them.
    Prevents deletion of admin ID 1 or the last administrator.
    """
    user = db.query_one("SELECT * FROM Users WHERE id = ?", (user_id,))
    if not user:
        raise ValueError("User not found.")

    if user['id'] == 1 or user['username'].lower() == 'admin':
        raise ValueError("The master administrator account cannot be deleted.")

    # Find linked Person
    person = db.query_one("SELECT id FROM Persons WHERE user_id = ?", (user_id,))
    unassigned_count = 0
    if person:
        p_id = person['id']
        # Unassign villages back to unassigned status
        unassigned_count = db.execute_non_query(
            """
            UPDATE Villages SET
                assigned_person_id = NULL,
                assigned_person_name = NULL,
                assigned_at = NULL,
                assignment_status = 'Unassigned'
            WHERE assigned_person_id = ?
            """,
            (p_id,)
        )
        db.execute_non_query(
            "UPDATE VillageAssignments SET status = 'Unassigned', unassigned_at = GETDATE() WHERE person_id = ? AND status = 'Active'",
            (p_id,)
        )
        db.execute_non_query("DELETE FROM Persons WHERE id = ?", (p_id,))

    db.execute_non_query("DELETE FROM Users WHERE id = ?", (user_id,))
    logger.info(f"User ID {user_id} deleted. {unassigned_count} villages unassigned.")
    return {
        "success": True,
        "deleted_user_id": user_id,
        "unassigned_villages_count": unassigned_count
    }


def toggle_user_status(user_id, is_active):
    """
    Activate or deactivate a user account.
    """
    user = db.query_one("SELECT * FROM Users WHERE id = ?", (user_id,))
    if not user:
        raise ValueError("User not found.")

    if user['id'] == 1 and not is_active:
        raise ValueError("The primary administrator account cannot be deactivated.")

    status_val = 1 if is_active else 0
    db.execute_non_query("UPDATE Users SET is_active = ? WHERE id = ?", (status_val, user_id))
    db.execute_non_query("UPDATE Persons SET is_active = ?, updated_at = GETDATE() WHERE user_id = ?", (status_val, user_id))

    return {"success": True, "user_id": user_id, "is_active": status_val}
