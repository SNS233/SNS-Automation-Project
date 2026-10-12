import json
import os
from flask import Blueprint, request, jsonify, send_file, session
from services.auth_service import login_required
from services.excel_service import (
    preview_uploaded_file,
    parse_and_import_file,
    get_import_batches_summary,
    get_batch_villages_paged,
    update_single_batch_village,
    correct_batch_with_excel,
    check_batch_delete_safety,
    delete_import_batch
)
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
@import_bp.route('/api/import/batches', methods=['GET'])
@login_required
def import_batches():
    try:
        batches = get_import_batches_summary()
        return jsonify({'success': True, 'batches': batches})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/batch/<int:batch_id>/villages', methods=['GET'])
@login_required
def get_batch_villages(batch_id):
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '', type=str)
        district = request.args.get('district', '', type=str)
        taluka = request.args.get('taluka', '', type=str)

        data = get_batch_villages_paged(
            batch_id=batch_id,
            page=page,
            page_size=page_size,
            search=search,
            district=district,
            taluka=taluka
        )
        if not data:
            return jsonify({'success': False, 'error': 'Batch not found.'}), 404

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/batch/<int:batch_id>/update-village', methods=['POST'])
@login_required
def update_batch_village(batch_id):
    try:
        req_data = request.get_json() or {}
        village_id = req_data.get('village_id')
        village_data = req_data.get('data') or req_data

        if not village_id:
            return jsonify({'success': False, 'error': 'Missing village_id'}), 400

        updated = update_single_batch_village(batch_id, village_id, village_data)
        return jsonify({'success': True, 'village': updated})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/batch/<int:batch_id>/correct', methods=['POST'])
@login_required
def correct_batch(batch_id):
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'Selected file has no filename.'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.xlsx', '.xls', '.csv'):
        return jsonify({'success': False, 'error': 'Invalid format. Please upload .xlsx, .xls, or .csv.'}), 400

    try:
        result = correct_batch_with_excel(batch_id, file)
        return jsonify({'success': True, 'result': result})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/batch/<int:batch_id>/check-delete', methods=['GET'])
@login_required
def check_delete(batch_id):
    try:
        safety = check_batch_delete_safety(batch_id)
        if not safety:
            return jsonify({'success': False, 'error': 'Batch not found.'}), 404
        return jsonify({'success': True, 'safety': safety})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@import_bp.route('/api/import/batch/<int:batch_id>/delete', methods=['POST'])
@login_required
def delete_batch(batch_id):
    try:
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized. Admin privileges required to delete an imported dataset.'}), 403

        req_data = request.get_json(silent=True) or {}
        force = bool(req_data.get('force') or request.form.get('force') in ('1', 'true', 'True'))

        result = delete_import_batch(batch_id, force=force)
        return jsonify(result)
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
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
