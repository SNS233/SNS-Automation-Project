import os
import sys
import unittest
from app import create_app
import db

def run_e2e_reopen_reassign_test():
    print("=" * 70)
    print("MANDATORY 10-STEP E2E REOPEN, REASSIGN AND REVIEW LINK VERIFICATION")
    print("=" * 70)

    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # Step 0: Ensure test users and persons are properly set up
    admin_user = db.query_one("SELECT id, username, full_name, role FROM Users WHERE id = 1")
    om_user = db.query_one("SELECT id, username, full_name, role FROM Users WHERE id = 5")
    mann_user = db.query_one("SELECT id, username, full_name, role FROM Users WHERE id = 6")
    om_person = db.query_one("SELECT id, name, user_id FROM Persons WHERE id = 8")
    mann_person = db.query_one("SELECT id, name, user_id FROM Persons WHERE id = 9")

    assert admin_user, "Admin user must exist"
    assert om_user, "Om Patel user must exist"
    assert mann_user, "Mann nayak user must exist"
    assert om_person, "Om Patel person record must exist"
    assert mann_person, "Mann nayak person record must exist"

    print(f"[SETUP] Admin: {admin_user['username']} (ID {admin_user['id']})")
    print(f"[SETUP] Surveyor 1: {om_user['username']} -> Person {om_person['name']} (ID {om_person['id']})")
    print(f"[SETUP] Surveyor 2: {mann_user['username']} -> Person {mann_person['name']} (ID {mann_person['id']})")

    # Pick or prepare a test village
    village_id = 19126
    test_url = "https://generate.snsies.com/villages/19126/review"
    
    # Reset village state cleanly before test
    db.execute_non_query("""
        UPDATE Villages 
        SET work_status = 'Pending', 
            kml_status = 'Pending',
            assigned_person_id = NULL,
            assigned_person_name = NULL,
            assignment_status = 'Unassigned',
            generated_review_url = ?,
            dugwells = 0,
            bores = 0,
            total_wells = 0,
            correction_reason = NULL,
            reopened_at = NULL,
            reopened_by = NULL
        WHERE id = ?
    """, (test_url, village_id))
    db.execute_non_query("DELETE FROM VillageAssignments WHERE village_id = ?", (village_id,))
    db.execute_non_query("DELETE FROM UserCompletionHistory WHERE village_id = ?", (village_id,))

    # STEP 1: Assign Village A to Om Patel (Person ID 8) as Admin
    print("\n--- STEP 1: Assign Village A to Om Patel (Person 8) ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user['id']
        sess['username'] = admin_user['username']
        sess['full_name'] = admin_user['full_name']
        sess['role'] = 'admin'

    assign_resp = client.post('/api/villages/assign', json={'village_ids': [village_id], 'person_id': om_person['id']})
    assert assign_resp.status_code == 200, f"Assignment failed: {assign_resp.data}"
    assign_data = assign_resp.get_json()
    assert assign_data['success'] is True
    print(f"-> Successfully assigned Village {village_id} to {om_person['name']}")

    # STEP 2: Verify review link is available for Om Patel in Excel Files / assigned villages
    print("\n--- STEP 2: Verify Review Link in Om Patel's Active Work List ---")
    with client.session_transaction() as sess:
        sess['user_id'] = om_user['id']
        sess['username'] = om_user['username']
        sess['full_name'] = om_user['full_name']
        sess['role'] = 'user'

    assigned_resp = client.get('/api/user/assigned-villages')
    assert assigned_resp.status_code == 200
    om_assigned = assigned_resp.get_json().get('items', [])
    target_in_om = next((v for v in om_assigned if v['id'] == village_id), None)
    assert target_in_om is not None, "Village A must appear in Om Patel's assigned list"
    assert target_in_om['generated_review_url'] == test_url, f"Expected review URL {test_url}, got {target_in_om.get('generated_review_url')}"
    print(f"-> Verified: Village {village_id} is in Om Patel's work list with genuine review URL: {target_in_om['generated_review_url']}")

    # STEP 3: Complete Village A as Om Patel
    print("\n--- STEP 3: Complete Village A as Om Patel ---")
    save_resp = client.post(f'/api/user/villages/{village_id}/save', json={
        'dugwells': 4,
        'bores': 6,
        'total_wells': 10,
        'remark': 'Initial survey completed by Om',
        'mark_completed': True,
        'status': 'Done'
    })
    assert save_resp.status_code == 200
    save_data = save_resp.get_json()
    assert save_data['success'] is True
    print(f"-> Successfully completed survey by Om Patel for Village {village_id}")

    # STEP 4: Verify Status Completed across DB, Dashboard, and User Work List
    print("\n--- STEP 4: Verify Status Completed ---")
    v_db = db.query_one("SELECT work_status, kml_status, dugwells, bores, total_wells, generated_review_url FROM Villages WHERE id = ?", (village_id,))
    assert v_db['work_status'] == 'Done'
    assert v_db['dugwells'] == 4 and v_db['bores'] == 6
    print(f"-> DB status confirmed: work_status={v_db['work_status']}, dugwells={v_db['dugwells']}, bores={v_db['bores']}")

    # Check Om's active work list (should be removed from pending)
    assigned_resp_after = client.get('/api/user/assigned-villages')
    om_active = assigned_resp_after.get_json().get('items', [])
    assert not any(v['id'] == village_id for v in om_active), "Completed village must NOT appear in Om's active work list"
    print(f"-> Verified: Village {village_id} successfully removed from Om Patel's active work list")

    # Check Dashboard Completed Villages endpoint as Admin
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user['id']
        sess['username'] = admin_user['username']
        sess['full_name'] = admin_user['full_name']
        sess['role'] = 'admin'

    comp_resp = client.get('/api/dashboard/completed-villages')
    assert comp_resp.status_code == 200
    comp_items = comp_resp.get_json().get('items', [])
    comp_v = next((item for item in comp_items if item['id'] == village_id), None)
    assert comp_v is not None, "Village must appear in Dashboard Completed Villages"
    assert comp_v['generated_review_url'] == test_url, "Genuine review URL must be displayed in Completed Villages"
    print(f"-> Verified: Appears in Dashboard Completed Villages with genuine review URL: {comp_v['generated_review_url']}")

    # STEP 5: Reopen Village A for Correction as Admin
    print("\n--- STEP 5: Reopen Village A for Correction as Admin ---")
    reopen_reason = "Incorrect well marking: 2 dugwells were misclassified as borewells."
    reopen_resp = client.post(f'/api/villages/{village_id}/reopen', json={
        'reason': reopen_reason
    })
    assert reopen_resp.status_code == 200, f"Reopen failed: {reopen_resp.data}"
    reopen_data = reopen_resp.get_json()
    assert reopen_data['success'] is True
    print(f"-> Reopen success: {reopen_data.get('message')}")

    # STEP 6: Verify Status changes to Correction Required and original review link & markings preserved
    print("\n--- STEP 6: Verify Correction Required & Review Link Preserved ---")
    v_reopened = db.query_one("SELECT work_status, kml_status, correction_reason, generated_review_url, dugwells, bores FROM Villages WHERE id = ?", (village_id,))
    assert v_reopened['work_status'] == 'Correction Required'
    assert v_reopened['kml_status'] == 'Correction Required'
    assert v_reopened['correction_reason'] == reopen_reason
    assert v_reopened['generated_review_url'] == test_url, "Genuine review link MUST be preserved upon reopening"
    assert v_reopened['dugwells'] == 4 and v_reopened['bores'] == 6, "Saved markings must be preserved"
    print(f"-> Verified: work_status='{v_reopened['work_status']}', reason='{v_reopened['correction_reason']}', URL preserved: '{v_reopened['generated_review_url']}'")

    # STEP 7: Reassign Village A to Mann nayak (Person 9, User 6)
    print("\n--- STEP 7: Reassign Village A to Mann nayak (Person 9) ---")
    reassign_reason = "Reassigned to Mann nayak for field re-survey and correction."
    reassign_resp = client.post(f'/api/villages/{village_id}/reassign', json={
        'new_person_id': mann_person['id'],
        'reason': reassign_reason
    })
    assert reassign_resp.status_code == 200, f"Reassign failed: {reassign_resp.data}"
    reassign_data = reassign_resp.get_json()
    assert reassign_data['success'] is True
    print(f"-> Reassign success: {reassign_data.get('message')}")

    # STEP 8: Verify Isolation: Disappears from Om Patel, Appears in Mann nayak with SAME review URL
    print("\n--- STEP 8: Verify Real-Time User List Isolation & Review Link ---")
    # As Om Patel:
    with client.session_transaction() as sess:
        sess['user_id'] = om_user['id']
        sess['username'] = om_user['username']
        sess['full_name'] = om_user['full_name']
        sess['role'] = 'user'

    om_list = client.get('/api/user/assigned-villages').get_json().get('items', [])
    assert not any(v['id'] == village_id for v in om_list), "Village A must NOT be visible to previous user Om Patel"
    print(f"-> Verified: Om Patel's work list does NOT contain Village {village_id}")

    # As Mann nayak:
    with client.session_transaction() as sess:
        sess['user_id'] = mann_user['id']
        sess['username'] = mann_user['username']
        sess['full_name'] = mann_user['full_name']
        sess['role'] = 'user'

    mann_list = client.get('/api/user/assigned-villages').get_json().get('items', [])
    mann_v = next((v for v in mann_list if v['id'] == village_id), None)
    assert mann_v is not None, "Village A MUST appear in new assignee Mann nayak's work list"
    assert mann_v['generated_review_url'] == test_url, f"Expected same review URL {test_url}, got {mann_v.get('generated_review_url')}"
    assert mann_v['work_status'] == 'Correction Required', "Status must reflect Correction Required"
    assert mann_v['correction_reason'] == reopen_reason, "Correction note must be displayed to new surveyor"
    print(f"-> Verified: Mann nayak sees Village {village_id} with SAME review link: {mann_v['generated_review_url']}")
    print(f"-> Verified: Correction reason visible: '{mann_v['correction_reason']}'")

    # STEP 9: Verify Assignment History Audit Endpoint
    print("\n--- STEP 9: Verify Audit History Endpoint ---")
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user['id']
        sess['username'] = admin_user['username']
        sess['full_name'] = admin_user['full_name']
        sess['role'] = 'admin'

    hist_resp = client.get(f'/api/villages/{village_id}/assignment-history')
    assert hist_resp.status_code == 200
    hist_data = hist_resp.get_json().get('data', {})
    assignments = hist_data.get('assignments', [])
    corrections = hist_data.get('corrections', [])
    assert len(assignments) >= 2, "Must record at least previous and new assignments"
    assert len(corrections) >= 1, "Must record correction reopen event"
    print(f"-> Audit history verified: {len(assignments)} assignments logged, {len(corrections)} correction audit records logged.")

    # STEP 10: Save Corrected Work as Mann nayak & Verify Only Village A becomes Completed
    print("\n--- STEP 10: Save Corrected Work as Mann nayak ---")
    with client.session_transaction() as sess:
        sess['user_id'] = mann_user['id']
        sess['username'] = mann_user['username']
        sess['full_name'] = mann_user['full_name']
        sess['role'] = 'user'

    save_corr_resp = client.post(f'/api/user/villages/{village_id}/save', json={
        'dugwells': 6,
        'bores': 4,
        'total_wells': 10,
        'remark': 'Corrected well markings verified in field by Mann',
        'mark_completed': True,
        'status': 'Done'
    })
    assert save_corr_resp.status_code == 200
    assert save_corr_resp.get_json()['success'] is True
    print(f"-> Corrected work saved successfully by Mann nayak")

    # Confirm final status and markings
    v_final = db.query_one("SELECT work_status, kml_status, dugwells, bores, total_wells, assigned_person_id FROM Villages WHERE id = ?", (village_id,))
    assert v_final['work_status'] == 'Done'
    assert v_final['dugwells'] == 6 and v_final['bores'] == 4
    assert v_final['assigned_person_id'] == mann_person['id']
    print(f"-> Final village status: work_status='{v_final['work_status']}', Dugwells={v_final['dugwells']}, Bores={v_final['bores']}, Assignee={mann_person['name']}")

    # Confirm it is removed from Mann's active work list
    mann_active_after = client.get('/api/user/assigned-villages').get_json().get('items', [])
    assert not any(v['id'] == village_id for v in mann_active_after), "Village A must now be removed from active work list"
    print(f"-> Verified: Village {village_id} removed from active work list after completion")

    print("\n" + "=" * 70)
    print("ALL 10 VERIFICATION CRITERIA PASSED SUCESSFULLY WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == '__main__':
    run_e2e_reopen_reassign_test()
