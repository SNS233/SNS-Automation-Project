<<<<<<< HEAD
import logging
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
from flask import Blueprint, request, jsonify
from services.auth_service import login_required, admin_required
from services.integration_adapter import marking_adapter
from db import check_db_health, query_all, query_one, execute_non_query

<<<<<<< HEAD
logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings_bp', __name__)

DEFAULT_SETTINGS = {
    'marking_portal_url': 'https://generate.snsies.com/',
    'auto_calc_total': 'true',
    'kml_storage_dir': 'uploads/kml',
    'app_name': 'Master Borewell & Tubewell Management Portal'
}

def ensure_settings_table():
    """Ensure the ApplicationSettings table exists with default seeds (safe, non-destructive)."""
    try:
        execute_non_query("""
        CREATE TABLE IF NOT EXISTS ApplicationSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        for k, v in DEFAULT_SETTINGS.items():
            existing = query_one("SELECT id FROM ApplicationSettings WHERE setting_key = ?", (k,))
            if not existing:
                execute_non_query(
                    "INSERT INTO ApplicationSettings (setting_key, setting_value) VALUES (?, ?)",
                    (k, v)
                )
    except Exception as e:
        logger.warning(f"Notice during ensure_settings_table: {e}")


@settings_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    """Retrieve system diagnostics and all application settings from database with safe defaults."""
    try:
        db_health = check_db_health()
        ensure_settings_table()

        rows = query_all("SELECT setting_key, setting_value FROM ApplicationSettings")
        settings_dict = {r['setting_key']: r['setting_value'] for r in rows} if rows else {}

        # Merge with defaults for any missing optional keys
        for k, v in DEFAULT_SETTINGS.items():
            if k not in settings_dict or settings_dict[k] is None:
                settings_dict[k] = v

=======
settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    try:
        db_health = check_db_health()
        rows = query_all("SELECT setting_key, setting_value, updated_at FROM ApplicationSettings")
        settings_dict = {r['setting_key']: r['setting_value'] for r in rows}
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        return jsonify({
            'success': True,
            'settings': settings_dict,
            'db_health': db_health
        })
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"Error loading settings: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f"Failed to retrieve settings: {str(e)}"}), 500
=======
        return jsonify({'success': False, 'error': str(e)}), 500
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1


@settings_bp.route('/api/settings', methods=['PUT'])
@login_required
@admin_required
def update_settings():
<<<<<<< HEAD
    """Update application settings in database using cross-database compatible upsert."""
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Invalid payload format. Expected JSON object.'}), 400

    try:
        ensure_settings_table()

        for key, val in data.items():
            clean_key = str(key).strip()
            clean_val = str(val).strip() if val is not None else ''

            if not clean_key:
                continue

            existing = query_one("SELECT id FROM ApplicationSettings WHERE setting_key = ?", (clean_key,))
            if existing:
                execute_non_query(
                    "UPDATE ApplicationSettings SET setting_value = ? WHERE setting_key = ?",
                    (clean_val, clean_key)
                )
            else:
                execute_non_query(
                    "INSERT INTO ApplicationSettings (setting_key, setting_value) VALUES (?, ?)",
                    (clean_key, clean_val)
                )

        # Verify that updated settings are committed to database
        saved_rows = query_all("SELECT setting_key, setting_value FROM ApplicationSettings")
        saved_dict = {r['setting_key']: r['setting_value'] for r in saved_rows} if saved_rows else {}

        logger.info(f"Settings successfully updated: {list(data.keys())}")
        return jsonify({
            'success': True,
            'message': 'Settings saved successfully.',
            'settings': saved_dict
        })
    except Exception as e:
        logger.error(f"Error saving settings: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f"Failed to save settings: {str(e)}"}), 500
=======
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
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1


@settings_bp.route('/api/settings/integration-payload/<int:village_id>', methods=['GET'])
@login_required
def get_integration_payload(village_id):
<<<<<<< HEAD
    """Retrieve external integration payload for a specific village."""
    try:
        village = query_one(
            "SELECT id, village_code, village_name, district_name, subdistrict_name, zone FROM Villages WHERE id = ?",
            (village_id,)
        )
=======
    try:
        village = query_one("SELECT id, village_code, village_name, district_name, subdistrict_name, zone FROM Villages WHERE id = ?", (village_id,))
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        if not village:
            return jsonify({'success': False, 'error': 'Village not found'}), 404
        
        payload = marking_adapter.prepare_assisted_payload(village)
        return jsonify({'success': True, 'data': payload})
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"Error generating integration payload for village {village_id}: {e}")
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        return jsonify({'success': False, 'error': str(e)}), 500
