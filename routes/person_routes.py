from flask import Blueprint, request, jsonify, session
from services.auth_service import login_required, admin_required
from services.person_service import (
    list_persons,
    get_person_by_id,
    create_person,
    update_person,
    delete_person,
    assign_villages,
    unassign_villages,
    get_unassigned_villages,
    get_assigned_villages
)

person_bp = Blueprint('person_bp', __name__)


@person_bp.route('/api/persons', methods=['GET'])
@login_required
def get_persons():
    """Retrieve list of all persons with their assigned village count."""
    try:
        persons = list_persons()
        return jsonify({'success': True, 'data': persons, 'persons': persons})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/persons', methods=['POST'])
@login_required
def add_person():
    """Add a new person."""
    try:
        data = request.get_json() or {}
        person = create_person(data)
        return jsonify({
            'success': True,
            'data': person,
            'person': person,
            'message': f"Person '{person.get('name')}' created successfully."
        }), 201
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/persons/<int:person_id>', methods=['GET'])
@login_required
def get_person(person_id):
    """Retrieve a specific person and their assigned villages."""
    try:
        person = get_person_by_id(person_id)
        if not person:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        return jsonify({'success': True, 'data': person, 'person': person})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/persons/<int:person_id>', methods=['PUT'])
@login_required
def edit_person(person_id):
    """Update person information."""
    try:
        data = request.get_json() or {}
        updated = update_person(person_id, data)
        return jsonify({
            'success': True,
            'data': updated,
            'message': f"Person '{updated.get('name')}' updated successfully."
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/persons/<int:person_id>', methods=['DELETE'])
@login_required
def remove_person(person_id):
    """Delete a person and unassign their villages."""
    try:
        res = delete_person(person_id)
        return jsonify({
            'success': True,
            'message': f"Person deleted successfully. {res['unassigned_villages_count']} village(s) unassigned.",
            'data': res
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/villages/assign', methods=['POST'])
@login_required
def assign_villages_endpoint():
    """Assign selected villages to a person."""
    try:
        data = request.get_json() or {}
        village_ids = data.get('village_ids', [])
        person_id = data.get('person_id')
        assigned_by = session.get('username', 'Admin')

        if not person_id:
            return jsonify({'success': False, 'error': 'Please select a person to assign.'}), 400
        if not village_ids:
            return jsonify({'success': False, 'error': 'Please select at least one village.'}), 400

        res = assign_villages(village_ids, person_id, assigned_by=assigned_by)
        return jsonify({
            'success': True,
            'message': f"Assigned {res['assigned_count']} village(s) to {res['person_name']}.",
            'assigned_count': res['assigned_count'],
            'person_name': res['person_name'],
            'data': res
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/villages/unassign', methods=['POST'])
@login_required
def unassign_villages_endpoint():
    """Unassign selected villages."""
    try:
        data = request.get_json() or {}
        village_ids = data.get('village_ids', [])
        changed_by = session.get('username', 'Admin')

        if not village_ids:
            return jsonify({'success': False, 'error': 'Please select at least one village to unassign.'}), 400

        res = unassign_villages(village_ids, changed_by=changed_by)
        return jsonify({
            'success': True,
            'message': f"Unassigned {res['unassigned_count']} village(s).",
            'unassigned_count': res['unassigned_count'],
            'data': res
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/villages/unassigned', methods=['GET'])
@login_required
def get_unassigned():
    """Get paginated unassigned villages."""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '', type=str)
        zone = request.args.get('zone', '', type=str)
        district = request.args.get('district', '', type=str)
        subdistrict = request.args.get('subdistrict', '', type=str)

        data = get_unassigned_villages(
            page=page,
            page_size=page_size,
            search=search,
            zone=zone,
            district=district,
            subdistrict=subdistrict
        )
        return jsonify({
            'success': True,
            'data': data,
            'items': data.get('items', []),
            'total_count': data.get('total_count', 0),
            'total_pages': data.get('total_pages', 1),
            'current_page': data.get('current_page', 1),
            'page_size': data.get('page_size', page_size)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@person_bp.route('/api/villages/assigned', methods=['GET'])
@login_required
def get_assigned():
    """Get paginated assigned villages."""
    try:
        person_id = request.args.get('person_id', None)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '', type=str)
        zone = request.args.get('zone', '', type=str)
        district = request.args.get('district', '', type=str)
        subdistrict = request.args.get('subdistrict', '', type=str)

        data = get_assigned_villages(
            person_id=person_id,
            page=page,
            page_size=page_size,
            search=search,
            zone=zone,
            district=district,
            subdistrict=subdistrict
        )
        return jsonify({
            'success': True,
            'data': data,
            'items': data.get('items', []),
            'total_count': data.get('total_count', 0),
            'total_pages': data.get('total_pages', 1),
            'current_page': data.get('current_page', 1),
            'page_size': data.get('page_size', page_size)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
