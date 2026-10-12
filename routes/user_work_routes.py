import logging
from flask import Blueprint, request, jsonify, session
from services.auth_service import login_required, admin_required
import services.user_work_service as user_work_service

logger = logging.getLogger(__name__)

user_work_bp = Blueprint('user_work_bp', __name__)


@user_work_bp.route('/api/user/assigned-villages', methods=['GET'])
@login_required
def get_user_assigned_villages():
    """
    Fetch active assigned villages exclusively for the currently authenticated user.
    Completed villages ('Done') are strictly excluded from the active work list.
    """
    try:
        user_id = session.get('user_id')
        search = request.args.get('search', '', type=str)
        district = request.args.get('district', '', type=str)
        subdistrict = request.args.get('subdistrict', '', type=str)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 100, type=int)

        data = user_work_service.get_user_assigned_villages(
            user_id=user_id,
            search=search,
            district=district,
            subdistrict=subdistrict,
            page=page,
            page_size=page_size
        )
        return jsonify({
            'success': True,
            'data': data,
            'items': data.get('items', []),
            'total_count': data.get('total_count', 0),
            'total_pages': data.get('total_pages', 1),
            'current_page': data.get('current_page', 1),
            'person_name': data.get('person_name', session.get('full_name'))
        })
    except Exception as e:
        logger.error(f"Error fetching user assigned villages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/user/metrics', methods=['GET'])
@login_required
def get_user_metrics():
    """
    Retrieve real-time metrics for the currently logged-in user:
    Assigned Villages and Pending Villages counts.
    """
    try:
        user_id = session.get('user_id')
        metrics = user_work_service.get_user_metrics(user_id)
        return jsonify({'success': True, 'data': metrics})
    except Exception as e:
        logger.error(f"Error fetching user metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/user/villages/<int:village_id>/ensure-link', methods=['POST'])
@login_required
def ensure_link(village_id):
    """
    Ensure the authentic review URL on https://generate.snsies.com/ is available.
    If not yet generated, generates on-demand and returns genuine URL.
    """
    try:
        link = user_work_service.ensure_village_review_link(village_id)
        return jsonify({'success': True, 'link': link})
    except Exception as e:
        logger.error(f"Error ensuring link for village {village_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/user/villages/<int:village_id>/check-completion', methods=['POST'])
@login_required
def check_single_completion(village_id):
    """
    Verify if a specific village has been saved and completed on the external marking portal.
    """
    try:
        user_id = session.get('user_id')
        user_name = session.get('full_name') or session.get('username')
        result = user_work_service.check_village_remote_completion(
            village_id=village_id,
            user_id=user_id,
            user_name=user_name
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"Error checking completion for village {village_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/user/villages/<int:village_id>/save', methods=['POST'])
@login_required
def save_user_village(village_id):
    """
    Save survey findings for an assigned village by Field Surveyor.
    Strictly updates only this specific village by unique ID.
    """
    try:
        user_id = session.get('user_id')
        user_name = session.get('full_name') or session.get('username')
        data = request.get_json() or {}
        result = user_work_service.save_surveyor_village(
            village_id=village_id,
            user_id=user_id,
            user_name=user_name,
            data=data
        )
        return jsonify(result)
    except PermissionError as pe:
        return jsonify({'success': False, 'error': str(pe)}), 403
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error saving surveyor village {village_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/user/check-completions', methods=['POST'])
@login_required
def check_all_completions():
    """
    Poll completion status across all active assigned villages for the logged-in user.
    """
    try:
        user_id = session.get('user_id')
        user_name = session.get('full_name') or session.get('username')
        completed = user_work_service.check_all_user_villages_completion(
            user_id=user_id,
            user_name=user_name
        )
        return jsonify({'success': True, 'completed': completed, 'count': len(completed)})
    except Exception as e:
        logger.error(f"Error checking user village completions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/admin/notifications', methods=['GET'])
@login_required
@admin_required
def get_notifications():
    """Retrieve completion notifications for the Admin Dashboard."""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() in ('true', '1')
        notifications = user_work_service.get_admin_notifications(unread_only=unread_only)
        return jsonify({'success': True, 'data': notifications, 'notifications': notifications})
    except Exception as e:
        logger.error(f"Error fetching admin notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/admin/notifications/mark-read', methods=['POST'])
@login_required
@admin_required
def mark_read():
    """Mark admin notifications as read."""
    try:
        data = request.get_json() or {}
        notification_ids = data.get('notification_ids')
        mark_all = data.get('mark_all', False)
        res = user_work_service.mark_notifications_read(notification_ids=notification_ids, mark_all=mark_all)
        return jsonify({'success': True, 'data': res})
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/user/history', methods=['GET'])
@login_required
def get_user_history():
    """
    Retrieve real-time completed village history for the logged-in user.
    Strictly returns: village_name and completion_date (DD-MM-YYYY in Indian local time).
    """
    try:
        user_id = session.get('user_id')
        history_items = user_work_service.get_user_history(user_id)
        return jsonify({
            'success': True,
            'items': history_items,
            'total_count': len(history_items)
        })
    except Exception as e:
        logger.error(f"Error fetching user history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_work_bp.route('/api/user/villages/<int:village_id>/complete', methods=['POST'])
@login_required
def mark_village_completed(village_id):
    """
    Explicitly mark village as completed for the authenticated user and record history.
    """
    try:
        user_id = session.get('user_id')
        user_name = session.get('full_name') or session.get('username')
        result = user_work_service.save_surveyor_village(
            village_id=village_id,
            user_id=user_id,
            user_name=user_name,
            data={'mark_completed': True, 'status': 'Done'}
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error marking village completed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

