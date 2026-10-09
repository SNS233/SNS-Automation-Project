from flask import Blueprint, request, jsonify, session
from services.auth_service import authenticate_user, get_current_user, login_required, change_password

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required.'}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({'success': False, 'error': 'Invalid username or password.'}), 401

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['full_name'] = user['full_name']

    import db
    person = db.query_one("SELECT id FROM Persons WHERE user_id = ? OR LOWER(name) = LOWER(?)", (user['id'], user.get('full_name') or user['username']))
    if person:
        session['person_id'] = person['id']
        if not person.get('user_id'):
            db.execute_non_query("UPDATE Persons SET user_id = ? WHERE id = ?", (user['id'], person['id']))

    return jsonify({
        'success': True,
        'user': user,
        'message': 'Logged in successfully.'
    })



@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not found.'}), 404
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'full_name': user.get('full_name') or user['username'],
            'role': user.get('role', 'user')
        }
    })


@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def update_password():
    data = request.get_json() or {}
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    
    success, msg = change_password(session['user_id'], old_pw, new_pw)
    if not success:
        return jsonify({'success': False, 'error': msg}), 400
    return jsonify({'success': True, 'message': msg})
