import re
import time
import logging
import threading
import requests
import db
from config import Config
from services.automation_service import DirectPortalClient
from services.sync_service import bump_state_version

logger = logging.getLogger(__name__)


def get_linked_person_for_user(user_id):
    """Find the Persons record associated with a given user ID or full name."""
    user = db.query_one("SELECT id, username, full_name FROM Users WHERE id = ?", (user_id,))
    if not user:
        return None
    person = db.query_one("SELECT * FROM Persons WHERE user_id = ?", (user_id,))
    if not person:
        # Fallback match by name
        cand_name = user.get('full_name') or user.get('username')
        person = db.query_one("SELECT * FROM Persons WHERE LOWER(name) = LOWER(?)", (cand_name,))
        if person and not person.get('user_id'):
            # Link permanently
            db.execute_non_query("UPDATE Persons SET user_id = ? WHERE id = ?", (user_id, person['id']))
    return person


def get_user_assigned_villages(user_id, search='', district='', subdistrict='', page=1, page_size=100):
    """
    Retrieve active assigned villages for a specific user.
    Strictly filters to only show villages currently assigned to this user
    where work_status != 'Done' and kml_status != 'Done'.
    """
    person = get_linked_person_for_user(user_id)
    if not person:
        return {
            "items": [],
            "total_count": 0,
            "total_pages": 1,
            "current_page": page,
            "page_size": page_size
        }

    person_id = person['id']
    where_clauses = [
        "v.assigned_person_id = ?",
        "(COALESCE(v.work_status, '') != 'Done' AND COALESCE(v.kml_status, '') != 'Done')"
    ]
    params = [person_id]

    if search:
        s_pat = f"%{search.strip()}%"
        where_clauses.append("(v.village_name LIKE ? OR v.village_code LIKE ?)")
        params.extend([s_pat, s_pat])

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
        v.generated_review_url,
        v.assigned_at,
        v.assignment_status
    FROM Villages v
    WHERE {where_sql}
    ORDER BY v.district_name ASC, v.village_name ASC
    LIMIT ? OFFSET ?
    """
    offset = (page - 1) * page_size
    query_params = list(params) + [page_size, offset]
    items = db.query_all(query_sql, query_params)

    return {
        "items": items,
        "total_count": total_count,
        "total_pages": max(1, (total_count + page_size - 1) // page_size),
        "current_page": page,
        "page_size": page_size,
        "person_name": person.get('name')
    }


def get_user_metrics(user_id):
    """
    Retrieve real-time workflow metrics for a specific user:
    - Assigned Villages (total active assigned)
    - Pending Villages (uncompleted assigned)
    """
    person = get_linked_person_for_user(user_id)
    if not person:
        return {"assigned_villages": 0, "pending_villages": 0, "completed_villages": 0}

    person_id = person['id']

    # Total assigned villages
    total_row = db.query_one(
        "SELECT COUNT(*) AS c FROM Villages WHERE assigned_person_id = ?",
        (person_id,)
    )
    assigned_count = total_row['c'] if total_row else 0

    # Pending villages (not yet done)
    pending_row = db.query_one(
        "SELECT COUNT(*) AS c FROM Villages WHERE assigned_person_id = ? AND (COALESCE(work_status, '') != 'Done' AND COALESCE(kml_status, '') != 'Done')",
        (person_id,)
    )
    pending_count = pending_row['c'] if pending_row else 0

    # Completed villages
    completed_row = db.query_one(
        "SELECT COUNT(*) AS c FROM Villages WHERE assigned_person_id = ? AND (COALESCE(work_status, '') = 'Done' OR COALESCE(kml_status, '') = 'Done')",
        (person_id,)
    )
    completed_count = completed_row['c'] if completed_row else 0

    return {
        "assigned_villages": assigned_count,
        "pending_villages": pending_count,
        "completed_villages": completed_count,
        "person_name": person.get('name')
    }


def ensure_village_review_link(village_id):
    """
    Ensure a village has an authentic generated review URL on https://generate.snsies.com/
    If not yet generated, connects to portal, triggers detection, and persists the genuine link.
    Never creates fake URLs.
    """
    village = db.query_one("SELECT id, village_name, village_code, generated_review_url FROM Villages WHERE id = ?", (village_id,))
    if not village:
        raise ValueError("Village not found.")

    if village.get('generated_review_url'):
        return village['generated_review_url']

    v_name = village['village_name']
    v_code = village.get('village_code', '')

    logger.info(f"Authenticating and generating genuine review link on https://generate.snsies.com/ for {v_name} ({v_code})...")
    client = DirectPortalClient(base_url="https://generate.snsies.com/")
    res = client.process_village(
        village_name=v_name,
        village_code=v_code,
        max_wait_seconds=90,
        auto_review_correct=False  # Do not auto-finalize; preserve review canvas for user
    )

    if res.get('status') == 'SUCCESS' and res.get('link'):
        link = res['link']
        db.execute_non_query(
            "UPDATE Villages SET generated_review_url = ?, updated_at = GETDATE() WHERE id = ?",
            (link, village_id)
        )
        logger.info(f"Persisted genuine review URL for {v_name}: {link}")
        return link
    else:
        err_msg = res.get('message', 'Generation failed on external portal')
        logger.warning(f"Could not generate review URL for {v_name}: {err_msg}")
        raise RuntimeError(err_msg)


def auto_generate_assigned_villages(village_ids):
    """Background helper to acquire genuine review URLs for newly assigned villages."""
    def worker():
        try:
            client = DirectPortalClient(base_url="https://generate.snsies.com/")
            for vid in village_ids:
                v = db.query_one("SELECT id, village_name, village_code, generated_review_url FROM Villages WHERE id = ?", (vid,))
                if not v or v.get('generated_review_url'):
                    continue
                try:
                    res = client.process_village(
                        village_name=v['village_name'],
                        village_code=v.get('village_code', ''),
                        max_wait_seconds=90,
                        auto_review_correct=False
                    )
                    if res.get('status') == 'SUCCESS' and res.get('link'):
                        db.execute_non_query(
                            "UPDATE Villages SET generated_review_url = ?, updated_at = GETDATE() WHERE id = ?",
                            (res['link'], vid)
                        )
                        logger.info(f"Background generated link for {v['village_name']}: {res['link']}")
                except Exception as inner_err:
                    logger.debug(f"Background link error for village {vid}: {inner_err}")
        except Exception as e:
            logger.error(f"Error in auto_generate_assigned_villages background worker: {e}")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


def check_village_remote_completion(village_id, user_id=None, user_name=None):
    """
    Check if a village has been reviewed and saved on the external marking portal.
    Detects completion:
    - By querying the village's review state on https://generate.snsies.com/
    - When confirmed completed, updates work_status = 'Done' & kml_status = 'Done',
      records notification in AdminNotifications, and records in ProcessingHistory.
    """
    v = db.query_one(
        "SELECT id, village_name, village_code, generated_review_url, work_status, kml_status, assigned_person_name, assigned_person_id FROM Villages WHERE id = ?",
        (village_id,)
    )
    if not v:
        return {"completed": False, "error": "Village not found"}

    if v.get('work_status') == 'Done' and v.get('kml_status') == 'Done':
        return {"completed": True, "already_done": True, "village_name": v['village_name']}

    rev_url = v.get('generated_review_url')
    v_name = v['village_name']
    v_code = v.get('village_code', '')
    active_user = user_name or v.get('assigned_person_name') or 'User'

    client = DirectPortalClient(base_url="https://generate.snsies.com/")
    client.login()

    is_completed = False
    v_rec_id = None

    if rev_url:
        m = re.search(r'/villages/(\d+)', rev_url)
        if m:
            v_rec_id = m.group(1)

    # 1. Primary Check: Inspect map-data on external portal for this exact remote ID
    if v_rec_id:
        try:
            map_resp = client.session.get(f"{client.base_url}/villages/{v_rec_id}/map-data", timeout=8)
            if map_resp.status_code == 200:
                mdata = map_resp.json()
                status_field = str(mdata.get('status', '')).strip().lower()
                # A village is completed IF AND ONLY IF status is 'finalized'
                # Unfinalized villages have status 'review' and must NOT be marked done
                if status_field in ('finalized', 'done', 'completed'):
                    is_completed = True
        except Exception as e:
            logger.debug(f"Map data inspection error for village {village_id} (remote {v_rec_id}): {e}")

    # 2. Secondary Check: Only if remote ID is not yet known, search portal by code/name
    if not v_rec_id and not is_completed:
        try:
            search_term = v_code if v_code else v_name
            if search_term:
                s_resp = client.session.get(f"{client.base_url}/?q={search_term}", timeout=8)
                s_row = client._find_village_row(s_resp.text, v_code, v_name)
                if s_row:
                    s_row_lower = s_row.lower()
                    # Strictly check for 'finalized' badge. 'review' or 'pending' badges mean NOT done!
                    if 'badge finalized' in s_row_lower or '>finalized<' in s_row_lower or 'badge done' in s_row_lower:
                        is_completed = True
                        m_link = re.search(r'href=[\'"](https://generate\.snsies\.com/villages/\d+/review)[\'"]', s_row)
                        if m_link and not rev_url:
                            cand_url = m_link.group(1)
                            # Ensure this URL is not mistakenly registered on another village
                            existing_url_village = db.query_one("SELECT id FROM Villages WHERE generated_review_url = ? AND id != ?", (cand_url, village_id))
                            if not existing_url_village:
                                db.execute_non_query(
                                    "UPDATE Villages SET generated_review_url = ?, updated_at = GETDATE() WHERE id = ?",
                                    (cand_url, village_id)
                                )
        except Exception as se:
            logger.debug(f"Search page inspection error for village {village_id}: {se}")

    if is_completed:
        # Mark as Done in database strictly for this unique village record
        db.execute_non_query(
            "UPDATE Villages SET work_status = 'Done', kml_status = 'Done', updated_at = GETDATE() WHERE id = ?",
            (village_id,)
        )

        # Notify Admin
        notification_msg = f"{active_user} completed {v_name}"
        db.execute_non_query(
            """
            INSERT INTO AdminNotifications (user_id, user_name, village_id, village_name, message, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, 0, GETDATE())
            """,
            (user_id, active_user, village_id, v_name, notification_msg)
        )

        # Record in ProcessingHistory
        try:
            db.execute_non_query(
                """
                INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by, created_at)
                VALUES (?, ?, ?, ?, ?, GETDATE())
                """,
                (village_id, 'In Progress', 'Done', f"Completed on external portal by {active_user}", active_user)
            )
        except Exception:
            pass

        # Bump global state version so Admin Dashboard and other clients reactively update
        bump_state_version()

        logger.info(f"Village '{v_name}' (ID {village_id}) detected as completed by '{active_user}'. Admin notified.")
        return {
            "completed": True,
            "village_id": village_id,
            "village_name": v_name,
            "user_name": active_user,
            "message": notification_msg
        }

    return {"completed": False, "village_id": village_id, "village_name": v_name}


def save_surveyor_village(village_id, user_id, user_name, data):
    """
    Save survey findings for an assigned village by Field Surveyor.
    - Strictly checks that the village is assigned to the current user (or caller is Admin).
    - Updates only this specific village record by unique ID (WHERE id = ?).
    - Independent status per village.
    - If mark_completed is True: marks work_status = 'Done' & kml_status = 'Done'.
    - If mark_completed is False: preserves pending status.
    - Notifies Admin and records in ProcessingHistory.
    - Bumps global state version for real-time reactivity.
    """
    v = db.query_one(
        "SELECT id, village_name, village_code, assigned_person_id, assigned_person_name, work_status, kml_status, dugwells, bores, total_wells, remark FROM Villages WHERE id = ?",
        (village_id,)
    )
    if not v:
        raise ValueError(f"Village with ID {village_id} does not exist.")

    # Verify authorization
    person = get_linked_person_for_user(user_id) if user_id else None
    user_row = db.query_one("SELECT role FROM Users WHERE id = ?", (user_id,)) if user_id else None
    is_admin = user_row and user_row.get('role') == 'admin'

    if not is_admin and person and v.get('assigned_person_id') != person['id']:
        raise PermissionError(f"Access denied. Village '{v['village_name']}' is not assigned to you.")

    # Parse survey fields
    def to_int(val, default_val=0):
        if val is None or str(val).strip() == '':
            return default_val
        try:
            return max(0, int(val))
        except (ValueError, TypeError):
            return default_val

    dugwells = to_int(data.get('dugwells'), v.get('dugwells') or 0)
    bores = to_int(data.get('bores'), v.get('bores') or 0)
    
    # Auto calculate or accept provided total
    if 'total_wells' in data and data['total_wells'] is not None and str(data['total_wells']).strip() != '':
        total_wells = to_int(data.get('total_wells'), dugwells + bores)
    else:
        total_wells = dugwells + bores

    remark = str(data.get('remark') or v.get('remark') or '').strip()
    mark_completed = data.get('mark_completed', True)
    status_str = str(data.get('status', '')).strip()

    if status_str in ('Done', 'Completed', 'Verified') or mark_completed:
        new_work_status = 'Done'
        new_kml_status = 'Done'
        action_note = f"Survey completed and saved by {user_name}"
    else:
        new_work_status = 'Not Done'
        new_kml_status = status_str if status_str else 'In Progress'
        action_note = f"Survey progress saved by {user_name}"

    # Atomic update on this specific village record only
    db.execute_non_query(
        """
        UPDATE Villages SET
            dugwells = ?,
            bores = ?,
            total_wells = ?,
            work_status = ?,
            kml_status = ?,
            remark = ?,
            last_processed_at = GETDATE(),
            updated_at = GETDATE()
        WHERE id = ?
        """,
        (dugwells, bores, total_wells, new_work_status, new_kml_status, remark, village_id)
    )

    # Insert notification for admin if completed
    if new_work_status == 'Done':
        notification_msg = f"{user_name} completed {v['village_name']}"
        db.execute_non_query(
            """
            INSERT INTO AdminNotifications (user_id, user_name, village_id, village_name, message, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, 0, GETDATE())
            """,
            (user_id, user_name, village_id, v['village_name'], notification_msg)
        )

    # Record in ProcessingHistory
    try:
        db.execute_non_query(
            """
            INSERT INTO ProcessingHistory (village_id, previous_status, new_status, action_note, changed_by, created_at)
            VALUES (?, ?, ?, ?, ?, GETDATE())
            """,
            (village_id, v.get('kml_status') or 'Pending', new_kml_status, action_note, user_name)
        )
    except Exception:
        pass

    # Bump global state version so Admin Dashboard and other users update reactively
    bump_state_version()

    logger.info(f"Village '{v['village_name']}' (ID {village_id}) survey saved as '{new_work_status}' by '{user_name}'.")
    return {
        "success": True,
        "village_id": village_id,
        "village_name": v['village_name'],
        "village_code": v['village_code'],
        "work_status": new_work_status,
        "kml_status": new_kml_status,
        "dugwells": dugwells,
        "bores": bores,
        "total_wells": total_wells,
        "remark": remark,
        "message": f"Village '{v['village_name']}' saved successfully."
    }


def check_all_user_villages_completion(user_id, user_name=None):
    """
    Check all active assigned villages for this user against the remote portal.
    Returns list of newly completed villages.
    """
    person = get_linked_person_for_user(user_id)
    if not person:
        return []

    person_id = person['id']
    active_user = user_name or person.get('name') or 'User'

    villages = db.query_all(
        "SELECT id FROM Villages WHERE assigned_person_id = ? AND (COALESCE(work_status, '') != 'Done' AND COALESCE(kml_status, '') != 'Done')",
        (person_id,)
    )

    completed_list = []
    for v in villages:
        res = check_village_remote_completion(v['id'], user_id=user_id, user_name=active_user)
        if res.get('completed') and not res.get('already_done'):
            completed_list.append(res)

    return completed_list


def get_admin_notifications(unread_only=False, limit=30):
    """Retrieve list of admin notifications for completed villages."""
    sql = """
    SELECT id, user_id, user_name, village_id, village_name, message, is_read, created_at
    FROM AdminNotifications
    """
    params = []
    if unread_only:
        sql += " WHERE is_read = 0"
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    return db.query_all(sql, params)


def mark_notifications_read(notification_ids=None, mark_all=False):
    """Mark one, multiple, or all notifications as read."""
    if mark_all:
        db.execute_non_query("UPDATE AdminNotifications SET is_read = 1 WHERE is_read = 0")
        return {"success": True, "message": "All notifications marked as read."}

    if notification_ids:
        clean = [int(nid) for nid in notification_ids if str(nid).isdigit()]
        if clean:
            placeholders = ",".join("?" * len(clean))
            db.execute_non_query(f"UPDATE AdminNotifications SET is_read = 1 WHERE id IN ({placeholders})", clean)
            return {"success": True, "marked_count": len(clean)}

    return {"success": True}
