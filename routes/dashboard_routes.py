from flask import Blueprint, jsonify, request, session
from services.auth_service import login_required
from services.village_service import get_dashboard_metrics
from services.sync_service import get_state_version
import services.user_work_service as user_work_service
import db

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/api/dashboard/metrics', methods=['GET'])
@login_required
def dashboard_metrics():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403
    try:
        zone = request.args.get('zone', '', type=str)
        metrics = get_dashboard_metrics(zone=zone)
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/system/heartbeat', methods=['GET'])
@login_required
def system_heartbeat():
    """
    Lightweight reactive heartbeat polled by clients every few seconds.
    Tells client whether database state has changed, and provides fresh live counts.
    """
    try:
        client_version = request.args.get('version', 0, type=int)
        server_version = get_state_version()
        has_changed = (client_version != server_version)

        role = session.get('role', 'user')
        user_id = session.get('user_id')

        # Fast unread notification count for admin
        unread_notifs = 0
        if role == 'admin':
            un_row = db.query_one("SELECT COUNT(*) AS c FROM AdminNotifications WHERE is_read = 0")
            unread_notifs = un_row['c'] if un_row else 0

        # Fast user-specific metrics if field surveyor
        user_metrics = {}
        if role == 'user' and user_id:
            user_metrics = user_work_service.get_user_metrics(user_id)

        return jsonify({
            'success': True,
            'server_version': server_version,
            'has_changed': has_changed,
            'unread_notifications': unread_notifs,
            'user_metrics': user_metrics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/dashboard/completed-villages', methods=['GET'])
@login_required
def dashboard_completed_villages():
    """
    Fetch all verified and completed villages with genuine review links.
    Admin-only access.
    """
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403
    try:
        query_sql = """
        SELECT 
            v.id,
            v.village_name,
            v.village_code,
            v.zone,
            v.district_name,
            v.subdistrict_name,
            v.assigned_person_id,
            v.assigned_person_name,
            v.dugwells,
            v.bores,
            v.total_wells,
            COALESCE(v.work_status, 'Done') AS work_status,
            COALESCE(v.kml_status, 'Done') AS kml_status,
            COALESCE(v.generated_review_url, (
                SELECT uch.review_url 
                FROM UserCompletionHistory uch 
                WHERE uch.village_id = v.id AND uch.review_url IS NOT NULL 
                ORDER BY uch.id DESC LIMIT 1
            )) AS generated_review_url,
            (
                SELECT uch.completion_date 
                FROM UserCompletionHistory uch 
                WHERE uch.village_id = v.id 
                ORDER BY uch.id DESC LIMIT 1
            ) AS completion_date,
            v.updated_at
        FROM Villages v
        WHERE (COALESCE(v.work_status, '') = 'Done' OR COALESCE(v.kml_status, '') IN ('Done', 'Verified', 'Marking Completed', 'Finalized'))
          AND (v.work_status IS NULL OR v.work_status != 'Correction Required')
        ORDER BY v.updated_at DESC, v.id DESC
        """
        items = db.query_all(query_sql)
        for item in items:
            if not item.get('completion_date') and item.get('updated_at'):
                item['completion_date'] = user_work_service.format_ist_date(item['updated_at'])
            if not item.get('completion_date'):
                item['completion_date'] = user_work_service.format_ist_date(None)

        return jsonify({'success': True, 'items': items, 'total_count': len(items)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

