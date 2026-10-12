import os
import functools
from flask import session, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
import db
import logging

logger = logging.getLogger(__name__)

def authenticate_user(username, password):
    """
    Authenticate user strictly against canonical database credentials.
    Rejects any invalid or outdated passwords with no hardcoded fallback bypasses.
    """
    if not username or not password:
        return None

    clean_username = str(username).strip()
    
    try:
        if db.is_db_available():
            user = db.query_one(
                "SELECT id, username, full_name, role, password_hash, is_active FROM Users WHERE LOWER(username) = LOWER(?) AND is_active = 1",
                (clean_username,)
            )
            if user:
                if check_password_hash(user['password_hash'], password):
                    return {
                        'id': user['id'],
                        'username': user['username'],
                        'full_name': user.get('full_name') or user['username'],
                        'role': user.get('role', 'user')
                    }
                else:
                    logger.warning(f"Failed authentication attempt for '{clean_username}': incorrect password.")
                    return None
            else:
                logger.warning(f"Failed authentication attempt: user '{clean_username}' not found or inactive.")
                return None
        else:
            logger.error("Authentication failed: database is not available.")
            return None
    except Exception as e:
        logger.error(f"Database error during authentication for '{clean_username}': {e}")
        return None


def get_current_user():
    """Retrieve current logged in user dict from session verified against database."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    try:
        if db.is_db_available():
            user = db.query_one(
                "SELECT id, username, full_name, role, is_active FROM Users WHERE id = ? AND is_active = 1",
                (user_id,)
            )
            if user:
                return user
    except Exception as e:
        logger.error(f"Error retrieving current user {user_id}: {e}")
    return None


def login_required(f):
    """Decorator to require user authentication for endpoints."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized. Please login.'}), 401
            from flask import redirect, url_for
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden. Admin privileges required.'}), 403
            from flask import redirect, url_for
            return redirect(url_for('dashboard_page'))
        return f(*args, **kwargs)
    return decorated_function


def change_password(user_id, old_password, new_password, confirm_password=None):
    """
    Verify old password and atomically update to new password in the database.
    Strictly replaces the old password hash so the previous password is never accepted.
    """
    if not user_id:
        return False, "Authentication session required."

    if not old_password:
        return False, "Current password is required."

    if not new_password:
        return False, "New password is required."

    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."

    if confirm_password is not None and str(new_password) != str(confirm_password):
        return False, "New password and confirmation password do not match."

    if old_password == new_password:
        return False, "New password must be different from current password."

    try:
        user = db.query_one("SELECT id, username, password_hash, is_active FROM Users WHERE id = ?", (user_id,))
        if not user:
            return False, "User account not found."

        if not user.get('is_active', 1):
            return False, "User account is inactive."

        # Verify old password
        if not check_password_hash(user['password_hash'], old_password):
            return False, "Current password is incorrect."

        # Securely hash new password
        new_hash = generate_password_hash(new_password)

        # Update password hash in database
        db.execute_non_query(
            "UPDATE Users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id)
        )

        # Verify database commit
        verified_user = db.query_one("SELECT password_hash FROM Users WHERE id = ?", (user_id,))
        if not verified_user or not check_password_hash(verified_user['password_hash'], new_password):
            return False, "Database failed to persist new password. Please try again."

        # Verify old password is no longer valid
        if check_password_hash(verified_user['password_hash'], old_password):
            return False, "Security verification failed: old password is still valid."

        logger.info(f"Password successfully changed for user ID {user_id} ('{user.get('username')}').")
        return True, "Password updated successfully."

    except Exception as e:
        logger.error(f"Database error during password change for user ID {user_id}: {e}")
        return False, f"Failed to update password: {str(e)}"
