import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import json
import logging
import db
from app import create_app
from services import person_service, user_work_service

logging.basicConfig(level=logging.INFO)

app = create_app()

def run_test():
    with app.app_context():
        print("=== STEP 1: PREPARE TEST DATA ===")
        # Get Om Patel
        user = db.query_one("SELECT * FROM Users WHERE username = 'ompatel'")
        assert user, "User ompatel must exist"
        person = db.query_one("SELECT * FROM Persons WHERE user_id = ?", (user['id'],))
        assert person, "Person record for ompatel must exist"
        person_id = person['id']
        user_id = user['id']
        print(f"User: {user['username']} (ID {user_id}), Person: {person['name']} (ID {person_id})")

        # Clear existing assignments for Om Patel
        db.execute_non_query("UPDATE Villages SET assigned_person_id = NULL, assigned_person_name = NULL, assignment_status = 'Unassigned', work_status = 'Not Done', kml_status = 'Pending' WHERE assigned_person_id = ?", (person_id,))

        # Pick 5 villages for test:
        # Village A: ID 19 (Bharkunda, code 511639, remote URL villages/54/review -> finalized)
        # Village B: ID 1 (Test Village 1, code 510001, remote URL villages/776/review -> review)
        # Village C: ID 5 (Test Village 5, code 510005, remote URL villages/777/review -> review)
        # Village D: ID 7 (Borisana, code 509002, remote URL villages/776/review -> review)
        # Village E: ID 8 (Pipariya, code 511852, remote URL villages/777/review -> review)
        test_vids = [19, 1, 5, 7, 8]

        # Reset all 5 to uncompleted state
        for vid in test_vids:
            db.execute_non_query(
                "UPDATE Villages SET work_status = 'Not Done', kml_status = 'Pending' WHERE id = ?",
                (vid,)
            )

        # Set valid test review links
        db.execute_non_query("UPDATE Villages SET generated_review_url = 'https://generate.snsies.com/villages/54/review' WHERE id = 19")
        db.execute_non_query("UPDATE Villages SET generated_review_url = 'https://generate.snsies.com/villages/776/review' WHERE id = 1")
        db.execute_non_query("UPDATE Villages SET generated_review_url = 'https://generate.snsies.com/villages/777/review' WHERE id = 5")
        db.execute_non_query("UPDATE Villages SET generated_review_url = 'https://generate.snsies.com/villages/776/review' WHERE id = 7")
        db.execute_non_query("UPDATE Villages SET generated_review_url = 'https://generate.snsies.com/villages/777/review' WHERE id = 8")

        # Assign all 5 to Om Patel
        person_service.assign_villages(test_vids, person_id, assigned_by='Admin')
        print(f"Assigned 5 villages to {person['name']}: {test_vids}")

        print("\n=== STEP 2: VERIFY INITIAL OM PATEL STATE ===")
        init_metrics = user_work_service.get_user_metrics(user_id)
        print("Initial Metrics:", init_metrics)
        assert init_metrics['assigned_villages'] == 5, f"Expected 5 assigned, got {init_metrics['assigned_villages']}"
        assert init_metrics['pending_villages'] == 5, f"Expected 5 pending, got {init_metrics['pending_villages']}"
        assert init_metrics['completed_villages'] == 0, f"Expected 0 completed, got {init_metrics['completed_villages']}"

        init_assigned = user_work_service.get_user_assigned_villages(user_id)
        assigned_names = [v['village_name'] for v in init_assigned['items']]
        print(f"Active assigned villages list ({len(assigned_names)} items): {assigned_names}")
        assert len(init_assigned['items']) == 5, f"Expected all 5 in active work list, got {len(init_assigned['items'])}"

        print("\n=== STEP 3: RUN COMPLETION CHECK ===")
        # Village 19 is remote 54 (status: finalized)
        # Village 1, 5, 7, 8 are remote 776 / 777 (status: review)
        completed = user_work_service.check_all_user_villages_completion(user_id, user_name='Om Patel')
        print(f"Check results: {len(completed)} villages completed:", completed)
        assert len(completed) == 1, f"Expected EXACTLY 1 completed village, got {len(completed)}"
        assert completed[0]['village_id'] == 19, f"Expected village 19 (Bharkunda) to be completed, got {completed[0]['village_id']}"
        assert completed[0]['village_name'] == 'Bharkunda'

        print("\n=== STEP 4: VERIFY OM PATEL POST-COMPLETION STATE ===")
        post_metrics = user_work_service.get_user_metrics(user_id)
        print("Post-Completion Metrics:", post_metrics)
        assert post_metrics['assigned_villages'] == 5, f"Expected 5 total assigned, got {post_metrics['assigned_villages']}"
        assert post_metrics['pending_villages'] == 4, f"Expected 4 pending, got {post_metrics['pending_villages']}"
        assert post_metrics['completed_villages'] == 1, f"Expected 1 completed, got {post_metrics['completed_villages']}"

        post_assigned = user_work_service.get_user_assigned_villages(user_id)
        remaining_vids = [v['id'] for v in post_assigned['items']]
        remaining_names = [v['village_name'] for v in post_assigned['items']]
        print(f"Remaining active work villages ({len(remaining_vids)} items): {remaining_names} (IDs: {remaining_vids})")
        assert len(post_assigned['items']) == 4, f"Expected exactly 4 remaining active villages, got {len(post_assigned['items'])}"
        assert 19 not in remaining_vids, "Completed village 19 must NOT be in active work list!"
        assert 1 in remaining_vids and 5 in remaining_vids and 7 in remaining_vids and 8 in remaining_vids, "Villages 1, 5, 7, 8 must remain in active work list!"

        # Verify all remaining review links are intact and working
        for v in post_assigned['items']:
            assert v['generated_review_url'], f"Village {v['village_name']} must retain its review URL!"
            print(f"  - {v['village_name']} (ID {v['id']}): URL = {v['generated_review_url']}")

        print("\n=== STEP 5: VERIFY ADMIN VISIBILITY ===")
        admin_assigned_view = person_service.get_assigned_villages(person_id=person_id)
        print(f"Admin view for Om Patel has {admin_assigned_view['total_count']} villages:")
        for v in admin_assigned_view['items']:
            print(f"  - {v['village_name']} (ID {v['id']}): work_status={v.get('work_status')}, updated_at={v.get('updated_at')}")

        # Confirm village 19 is marked Done in Admin view
        v19_admin = next((v for v in admin_assigned_view['items'] if v['id'] == 19), None)
        assert v19_admin, "Village 19 must appear in Admin assigned view"
        assert v19_admin['work_status'] == 'Done', f"Village 19 must be Done in Admin view, got {v19_admin['work_status']}"

        # Confirm other 4 are Not Done in Admin view
        for other_id in [1, 5, 7, 8]:
            v_admin = next((v for v in admin_assigned_view['items'] if v['id'] == other_id), None)
            assert v_admin, f"Village {other_id} must appear in Admin view"
            assert v_admin['work_status'] != 'Done', f"Village {other_id} must NOT be Done in Admin view, got {v_admin['work_status']}"

        # Check Admin Notifications
        notifs = user_work_service.get_admin_notifications()
        print(f"Admin Notifications count: {len(notifs)}")
        latest_notif = notifs[0] if notifs else None
        print(f"Latest Notification: {latest_notif}")
        assert latest_notif and 'Bharkunda' in latest_notif['message'] and 'Om Patel' in latest_notif['message'], "Admin notification must record Om Patel completed Bharkunda"

        print("\n=== ALL MANDATORY TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_test()
