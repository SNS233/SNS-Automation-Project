import json
import os
from flask import Blueprint, request, jsonify, send_file
from services.auth_service import login_required
from services.excel_service import preview_uploaded_file, parse_and_import_file
from config import Config
import db

import_bp = Blueprint('import_bp', __name__)

@import_bp.route('/api/import/preview', methods=['POST'])
@login_required
def preview_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'Selected file has no filename.'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.xlsx', '.xls', '.csv'):
        return jsonify({'success': False, 'error': 'Invalid file format. Please upload .xlsx, .xls, or .csv.'}), 400

    try:
        preview_data = preview_uploaded_file(file)
        return jsonify({'success': True, 'preview': preview_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/process', methods=['POST'])
@login_required
def process_import():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

    file = request.files['file']
    duplicate_mode = request.form.get('duplicate_mode', 'skip')
    mappings_json = request.form.get('column_mappings', '{}')

    try:
        column_mappings = json.loads(mappings_json)
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid column mappings format.'}), 400

    try:
        result = parse_and_import_file(
            file_storage_or_path=file,
            column_mappings=column_mappings,
            duplicate_mode=duplicate_mode,
            batch_filename=file.filename
        )
        return jsonify({'success': True, 'result': result})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/history', methods=['GET'])
@login_required
def import_history():
    try:
        batches = db.query_all("""
        SELECT 
            id, filename, total_rows, valid_rows, invalid_rows, duplicate_rows, 
            status, error_report_path, created_at
        FROM ImportBatches
        ORDER BY created_at DESC
        """)
        
        # Add clean error report filename
        for b in batches:
            if b.get('error_report_path'):
                b['error_report_name'] = os.path.basename(b['error_report_path'])
            else:
                b['error_report_name'] = None
                
        return jsonify({'success': True, 'batches': batches})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/errors/<filename>', methods=['GET'])
@login_required
def download_error_report(filename):
    file_path = Config.ERROR_REPORT_DIR / filename
    if not file_path.exists():
        return jsonify({'success': False, 'error': 'Error report file not found.'}), 404

    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
