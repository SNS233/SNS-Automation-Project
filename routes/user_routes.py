import logging
from flask import Blueprint, request, jsonify
from services.auth_service import login_required, admin_required
import services.user_service as user_service

logger = logging.getLogger(__name__)

user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/api/admin/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Retrieve all users for User Settings management."""
    try:
        users = user_service.list_users()
        return jsonify({'success': True, 'data': users})
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/api/admin/users', methods=['POST'])
@login_required
@admin_required
def add_user():
    """Create a new user and sync with Assign Person system."""
    try:
        data = request.get_json() or {}
        new_user = user_service.create_user(data)
        return jsonify({
            'success': True,
            'message': f"User '{new_user['username']}' created successfully.",
            'data': new_user
        }), 201
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    """Retrieve details for a specific user."""
    try:
        user = user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found.'}), 404
        return jsonify({'success': True, 'data': user})
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user_route(user_id):
    """Update user credentials or active state."""
    try:
        data = request.get_json() or {}
        updated_user = user_service.update_user(user_id, data)
        return jsonify({
            'success': True,
            'message': f"User '{updated_user['username']}' updated successfully.",
            'data': updated_user
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user_route(user_id):
    """Remove a user and unassign their villages."""
    try:
        result = user_service.delete_user(user_id)
        return jsonify({
            'success': True,
            'message': 'User deleted and assigned villages unassigned successfully.',
            'data': result
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_status(user_id):
    """Activate or deactivate a user account."""
    try:
        data = request.get_json() or {}
        is_active = data.get('is_active', True)
        result = user_service.toggle_user_status(user_id, is_active)
        return jsonify({
            'success': True,
            'message': f"User status {'activated' if is_active else 'deactivated'} successfully.",
            'data': result
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error toggling user {user_id} status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
