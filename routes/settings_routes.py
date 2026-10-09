from flask import Blueprint, request, jsonify
from services.auth_service import login_required, admin_required
from services.integration_adapter import marking_adapter
from db import check_db_health, query_all, query_one, execute_non_query

settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    try:
        db_health = check_db_health()
        rows = query_all("SELECT setting_key, setting_value, updated_at FROM ApplicationSettings")
        settings_dict = {r['setting_key']: r['setting_value'] for r in rows}
        return jsonify({
            'success': True,
            'settings': settings_dict,
            'db_health': db_health
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/settings', methods=['PUT'])
@login_required
@admin_required
def update_settings():
    data = request.get_json() or {}
    try:
        for key, val in data.items():
            execute_non_query("""
            IF EXISTS (SELECT 1 FROM ApplicationSettings WHERE setting_key = ?)
                UPDATE ApplicationSettings SET setting_value = ?, updated_at = GETDATE() WHERE setting_key = ?
            ELSE
                INSERT INTO ApplicationSettings (setting_key, setting_value, updated_at) VALUES (?, ?, GETDATE())
            """, (key, str(val), key, key, str(val)))

        return jsonify({'success': True, 'message': 'Settings saved successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/settings/integration-payload/<int:village_id>', methods=['GET'])
@login_required
def get_integration_payload(village_id):
    try:
        village = query_one("SELECT id, village_code, village_name, district_name, subdistrict_name, zone FROM Villages WHERE id = ?", (village_id,))
        if not village:
            return jsonify({'success': False, 'error': 'Village not found'}), 404
        
        payload = marking_adapter.prepare_assisted_payload(village)
        return jsonify({'success': True, 'data': payload})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
