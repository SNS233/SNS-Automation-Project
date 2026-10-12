import json
import os
from flask import Blueprint, request, jsonify, send_file
from services.auth_service import login_required
from services.kml_service import save_kml_for_village
from services.integration_adapter import marking_adapter
from config import Config
import db

kml_bp = Blueprint('kml_bp', __name__)

@kml_bp.route('/api/kml/upload/<int:village_id>', methods=['POST'])
@login_required
def upload_kml(village_id):
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No KML file provided.'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'No file selected.'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.kml', '.kmz', '.xml'):
        return jsonify({'success': False, 'error': 'File must have .kml or .kmz extension.'}), 400

    try:
        # Check village exists
        village = db.query_one("SELECT * FROM Villages WHERE id = ?", (village_id,))
        if not village:
            return jsonify({'success': False, 'error': 'Village not found.'}), 404

        result = save_kml_for_village(
            village_id=village_id,
            file_storage_or_bytes=file,
            original_filename=file.filename,
            village_code=village['village_code']
        )

        # Check match confidence
        match_info = marking_adapter.verify_kml_match(
            village=village,
            kml_filename=file.filename,
            kml_placemarks=result['total_placemarks']
        )
        result['match_info'] = match_info

        return jsonify({'success': True, 'data': result, 'message': 'KML processed and linked successfully.'})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@kml_bp.route('/api/kml/download/<int:kml_id>', methods=['GET'])
def download_kml(kml_id):
    """Download stored KML file (accessible for export hyperlinks or logged in user)."""
    kml_row = db.query_one("SELECT file_path, original_filename FROM KMLFiles WHERE id = ?", (kml_id,))
    if not kml_row:
        return jsonify({'success': False, 'error': 'KML record not found.'}), 404

    file_path = kml_row['file_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'Physical file missing from server.'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=kml_row['original_filename'],
        mimetype='application/vnd.google-earth.kml+xml'
    )


@kml_bp.route('/api/kml/geojson/<int:village_id>', methods=['GET'])
@login_required
def get_village_geojson(village_id):
    kml_row = db.query_one("SELECT geojson_data, bounds_json FROM KMLFiles WHERE village_id = ? AND is_active = 1", (village_id,))
    if not kml_row or not kml_row['geojson_data']:
        return jsonify({'success': False, 'error': 'No active KML found for this village.'}), 404

    try:
        geojson = json.loads(kml_row['geojson_data'])
        bounds = json.loads(kml_row['bounds_json']) if kml_row['bounds_json'] else None
        return jsonify({
            'success': True,
            'geojson': geojson,
            'bounds': bounds
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@kml_bp.route('/api/kml/list', methods=['GET'])
@login_required
def list_kml_files():
    try:
        search = request.args.get('search', '')
        where_clause = "1=1"
        params = []
        if search:
            where_clause += " AND (k.original_filename LIKE ? OR v.village_name LIKE ? OR v.village_code LIKE ?)"
            s = f"%{search.strip()}%"
            params.extend([s, s, s])

        files = db.query_all(f"""
        SELECT 
            k.id,
            k.village_id,
            k.village_code,
            k.original_filename,
            k.stored_filename,
            k.file_size,
            k.point_count,
            k.polygon_count,
            k.linestring_count,
            k.total_placemarks,
            k.version,
            k.is_active,
            k.created_at,
            v.village_name,
            v.district_name,
            v.subdistrict_name,
            v.kml_status
        FROM KMLFiles k
        JOIN Villages v ON k.village_id = v.id
        WHERE {where_clause}
        ORDER BY k.created_at DESC
        """, params)

        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
