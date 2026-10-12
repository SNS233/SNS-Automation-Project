from flask import Blueprint, request, jsonify, session
from services.auth_service import login_required
from services.village_service import (
    get_villages_paged,
    get_village_by_id,
    update_village,
    update_village_status,
    bulk_update_status,
    get_queue_navigation,
    delete_village,
<<<<<<< HEAD
    bulk_delete_unassigned_villages,
    reopen_completed_village,
    get_village_correction_history,
    reassign_village,
    get_village_full_assignment_history
)
import services.user_work_service as user_work_service
=======
    bulk_delete_unassigned_villages
)
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
import db

village_bp = Blueprint('village_bp', __name__)

@village_bp.route('/api/villages', methods=['GET'])
@login_required
def list_villages():
<<<<<<< HEAD
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    search = request.args.get('search', '', type=str)
    district = request.args.get('district', '', type=str)
    subdistrict = request.args.get('subdistrict', '', type=str)
    zone = request.args.get('zone', '', type=str)
    status = request.args.get('status', '', type=str)
<<<<<<< HEAD
    person_id = request.args.get('person_id', None, type=int)
    assignment_status = request.args.get('assignment_status', '', type=str)
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    sort_by = request.args.get('sort_by', 'district_name', type=str)
    sort_dir = request.args.get('sort_dir', 'asc', type=str)

    try:
        data = get_villages_paged(
            page=page,
            page_size=page_size,
            search=search,
            district=district,
            subdistrict=subdistrict,
            zone=zone,
            status=status,
<<<<<<< HEAD
            person_id=person_id,
            assignment_status=assignment_status,
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/<int:village_id>', methods=['GET'])
@login_required
def get_village(village_id):
    try:
        village = get_village_by_id(village_id)
        if not village:
            return jsonify({'success': False, 'error': 'Village not found'}), 404
        return jsonify({'success': True, 'village': village})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/<int:village_id>', methods=['PUT'])
@login_required
def update_village_endpoint(village_id):
    data = request.get_json() or {}
    changed_by = session.get('username', 'System')
    try:
        updated = update_village(village_id, data, changed_by=changed_by)
        return jsonify({'success': True, 'village': updated, 'message': 'Village updated successfully.'})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/<int:village_id>', methods=['DELETE'])
@login_required
def delete_village_endpoint(village_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin privileges required to delete a village.'}), 403

    try:
        res = delete_village(village_id, changed_by=session.get('username', 'Admin'))
        return jsonify({
            'success': True,
            'message': f"Village '{res.get('village_name')}' deleted successfully.",
            'data': res
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


<<<<<<< HEAD
@village_bp.route('/api/villages/<int:village_id>/reopen', methods=['POST'])
@login_required
def reopen_village_endpoint(village_id):
    """
    Admin-only: Reopen a completed village and send it for correction.
    Requires correction reason, and optionally reassigns to another field surveyor.
    """
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin privileges required to reopen villages.'}), 403

    data = request.get_json() or {}
    reason = (data.get('reason') or '').strip()
    new_person_id = data.get('new_person_id') if data.get('new_person_id') is not None else data.get('person_id')
    reopened_by = session.get('username', 'Admin')

    if not reason:
        return jsonify({'success': False, 'error': 'Correction reason is required.'}), 400

    try:
        res = reopen_completed_village(
            village_id=village_id,
            reason=reason,
            new_person_id=new_person_id,
            reopened_by=reopened_by
        )
        return jsonify({
            'success': True,
            'message': f"Village '{res.get('village_name')}' reopened and sent for correction.",
            'data': res
        }), 200
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/<int:village_id>/corrections', methods=['GET'])
@login_required
def get_village_corrections_endpoint(village_id):
    """Retrieve full audit history of corrections for a village."""
    try:
        corrections = get_village_correction_history(village_id)
        return jsonify({'success': True, 'corrections': corrections, 'data': corrections})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/<int:village_id>/reassign', methods=['POST'])
@login_required
def reassign_village_endpoint(village_id):
    """
    Reassign a village to another surveyor.
    Admin-only operation.
    """
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403

    data = request.get_json() or {}
    new_person_id = data.get('person_id') or data.get('new_person_id')
    reason = data.get('reason')
    reassigned_by = session.get('username', 'Admin')

    if not new_person_id:
        return jsonify({'success': False, 'error': 'Please select a new surveyor to reassign.'}), 400

    try:
        res = reassign_village(
            village_id=village_id,
            new_person_id=new_person_id,
            reassigned_by=reassigned_by,
            reason=reason
        )
        return jsonify({
            'success': True,
            'message': f"Village '{res.get('village_name')}' successfully reassigned to {res.get('new_person')}.",
            'data': res
        }), 200
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/<int:village_id>/assignment-history', methods=['GET'])
@login_required
def get_village_assignment_history_endpoint(village_id):
    """
    Retrieve full audit history of assignments, reassignments, corrections and processing events.
    Admin-only operation.
    """
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403

    try:
        history_data = get_village_full_assignment_history(village_id)
        if not history_data:
            return jsonify({'success': False, 'error': 'Village not found.'}), 404
        return jsonify({'success': True, 'data': history_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
@village_bp.route('/api/villages/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_villages_endpoint():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin privileges required to delete villages.'}), 403

    data = request.get_json() or {}
    village_ids = data.get('village_ids', [])
    if not village_ids or not isinstance(village_ids, list):
        return jsonify({'success': False, 'error': 'No village IDs provided for deletion.'}), 400

    unassigned_only = bool(data.get('unassigned_only', True))
    changed_by = session.get('username', 'Admin')

    try:
        res = bulk_delete_unassigned_villages(village_ids, changed_by=changed_by, unassigned_only=unassigned_only)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@village_bp.route('/api/villages/<int:village_id>/status', methods=['POST'])
@login_required
def change_status(village_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    note = data.get('action_note', 'Status updated')
    override_no_kml = bool(data.get('override_no_kml', False))
    changed_by = session.get('username', 'System')

    if not new_status:
        return jsonify({'success': False, 'error': 'Status is required.'}), 400

    try:
        update_village_status(village_id, new_status, action_note=note, changed_by=changed_by, override_no_kml=override_no_kml)
        return jsonify({'success': True, 'message': f'Status changed to {new_status}'})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/bulk-status', methods=['POST'])
@login_required
def bulk_status():
    data = request.get_json() or {}
    village_ids = data.get('village_ids', [])
    new_status = data.get('status')
    note = data.get('action_note', 'Bulk status update')
    changed_by = session.get('username', 'System')

    if not village_ids or not new_status:
        return jsonify({'success': False, 'error': 'Village IDs and status are required.'}), 400

    try:
        updated_count = bulk_update_status(village_ids, new_status, note=note, changed_by=changed_by)
        return jsonify({'success': True, 'updated_count': updated_count, 'message': f'Updated {updated_count} villages to {new_status}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/queue/next', methods=['GET'])
@login_required
def get_queue():
    current_id = request.args.get('current_id', None, type=int)
    try:
        nav = get_queue_navigation(current_id)
        return jsonify({'success': True, 'data': nav})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/filters', methods=['GET'])
@login_required
def get_filter_options():
    try:
        districts = [r['district_name'] for r in db.query_all("SELECT DISTINCT district_name FROM Villages WHERE district_name IS NOT NULL ORDER BY district_name")]
        subdistricts = [r['subdistrict_name'] for r in db.query_all("SELECT DISTINCT subdistrict_name FROM Villages WHERE subdistrict_name IS NOT NULL ORDER BY subdistrict_name")]
<<<<<<< HEAD
        zones = ['GPIC', 'KPIC', 'VPIC', 'RPIC']
        extra_zones = [r['zone'] for r in db.query_all("SELECT DISTINCT zone FROM Villages WHERE zone IS NOT NULL AND zone <> '' AND UPPER(TRIM(zone)) NOT IN ('GPIC', 'KPIC', 'VPIC', 'RPIC') ORDER BY zone")]
        if extra_zones:
            zones.append('Other / Unassigned')
        persons = [{'id': r['id'], 'name': r['name']} for r in db.query_all("SELECT id, name FROM Persons WHERE is_active = 1 ORDER BY name ASC")]
=======
        zones = [r['zone'] for r in db.query_all("SELECT DISTINCT zone FROM Villages WHERE zone IS NOT NULL AND zone <> '' ORDER BY zone")]
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        return jsonify({
            'success': True,
            'districts': districts,
            'subdistricts': subdistricts,
<<<<<<< HEAD
            'zones': zones,
            'persons': persons
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@village_bp.route('/api/villages/<int:village_id>/review-url', methods=['GET'])
@login_required
def get_village_review_url(village_id):
    """
    Retrieve genuine stored review URL and saved markings for a village.
    Protected by Admin authentication (or assigned surveyor).
    Never generates a fake URL.
    """
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        village = db.query_one("""
            SELECT id, village_name, village_code, zone, district_name, subdistrict_name,
                   assigned_person_id, assigned_person_name,
                   dugwells, bores, total_wells, work_status, kml_status,
                   generated_review_url, updated_at
            FROM Villages WHERE id = ?
        """, (village_id,))
        if not village:
            return jsonify({'success': False, 'error': 'Village not found'}), 404

        # If user is not admin, ensure village is assigned to user
        if role != 'admin':
            person = user_work_service.get_linked_person_for_user(user_id)
            if not person or village.get('assigned_person_id') != person['id']:
                return jsonify({'success': False, 'error': 'Access denied'}), 403

        review_url = village.get('generated_review_url')
        if not review_url:
            uch = db.query_one("SELECT review_url FROM UserCompletionHistory WHERE village_id = ? AND review_url IS NOT NULL ORDER BY id DESC LIMIT 1", (village_id,))
            if uch and uch.get('review_url'):
                review_url = uch['review_url']

        return jsonify({
            'success': True,
            'village_id': village['id'],
            'village_name': village['village_name'],
            'village_code': village.get('village_code'),
            'review_url': review_url,
            'dugwells': village.get('dugwells', 0),
            'bores': village.get('bores', 0),
            'total_wells': village.get('total_wells', 0),
            'work_status': village.get('work_status'),
            'kml_status': village.get('kml_status'),
            'has_review_url': bool(review_url)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

=======
            'zones': zones
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
