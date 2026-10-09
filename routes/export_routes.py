import datetime
import re
from flask import Blueprint, request, send_file, jsonify
from services.auth_service import login_required
from services.excel_service import generate_excel_export
import db

export_bp = Blueprint('export_bp', __name__)

@export_bp.route('/api/export/excel', methods=['GET', 'POST'])
@login_required
def export_excel():
    filters = {}
    if request.method == 'POST':
        data = request.get_json() or {}
        filters['selected_ids'] = data.get('selected_ids', [])
        filters['district'] = data.get('district', '')
        filters['subdistrict'] = data.get('subdistrict', '')
        filters['status'] = data.get('status', '')
        filters['zone'] = data.get('zone', '')
        filters['person_id'] = data.get('person_id', '')
        filters['export_type'] = data.get('export_type', '')
    else:
        filters['district'] = request.args.get('district', '')
        filters['subdistrict'] = request.args.get('subdistrict', '')
        filters['status'] = request.args.get('status', '')
        filters['zone'] = request.args.get('zone', '')
        filters['person_id'] = request.args.get('person_id', '')
        filters['export_type'] = request.args.get('export_type', '')
        sel = request.args.get('selected_ids', '')
        if sel:
            filters['selected_ids'] = [s.strip() for s in sel.split(',') if s.strip()]

    try:
        base_url = request.host_url.rstrip('/')
        excel_stream = generate_excel_export(filters=filters, base_url=base_url)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"Village_GEB_Data_{timestamp}.xlsx"

        if filters.get('person_id'):
            person_row = db.query_one("SELECT name FROM Persons WHERE id = ?", (filters['person_id'],))
            p_name = person_row['name'] if person_row else f"Person_{filters['person_id']}"
            safe_p_name = re.sub(r'[^\w\-]', '_', p_name)
            download_name = f"Village_GEB_Data_{safe_p_name}_{timestamp}.xlsx"
        elif filters.get('export_type') == 'all_persons':
            download_name = f"Village_GEB_Data_All_Persons_{timestamp}.xlsx"

        return send_file(
            excel_stream,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
