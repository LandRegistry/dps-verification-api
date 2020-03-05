from datetime import datetime
from flask import request, Blueprint, jsonify
from flask_negotiate import consumes, produces

from verification_api.app import app
from verification_api.exceptions import ApplicationError
from verification_api.services import verification_service as service
from verification_api.dependencies.metric_api import insert_metric_event, handle_dataset_access_metrics


verification_bp = Blueprint('verification_bp', __name__)


@verification_bp.route('/worklist', methods=['GET'])
@produces('application/json')
def get_worklist():
    try:
        app.logger.info("Getting all work-list")
        pending = service.get_pending()
        return jsonify(pending)
    except ApplicationError as error:
        error_message = 'Failed to retrieve worklist - {}'.format(error.message)
        app.logger.error(error_message)
        return jsonify(error=error_message), error.http_code


@verification_bp.route('/case', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def insert_case():
    try:
        case_details = request.get_json(force=True)
        app.logger.info("Inserting into worklist table for user {}".format(case_details['user_id']))
        case_id = service.insert_case(case_details)
        result = {'message': 'user {} added to dps worklist'.format(case_details['user_id']),
                  'case_id': case_id}
        case_details['registration_data']['date_added'] = str(datetime.now())

        insert_metric_event('application received', case_details)

        return jsonify(result), 201

    except ApplicationError as error:
        error_msg = 'Failed to insert case - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/case/<case_id>', methods=['GET'])
@produces('application/json')
def get_case_by_id(case_id):
    try:
        app.logger.info("Getting details for id: {}".format(case_id))
        result = service.get_pending_by_id(case_id)
        return jsonify(result)
    except ApplicationError as error:
        error_message = "Failed to get case '{}' - {}".format(case_id, error.message)
        app.logger.error(error_message)
        return jsonify(error=error_message), error.http_code


@verification_bp.route('/case/<case_id>/approve', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def approve_case(case_id):
    try:
        approval = request.get_json(force=True)
        app.logger.info('Approving case {}, by: {}'.format(case_id, approval['staff_id']))
        result = service.dps_action('Approve', case_id, approval)
        if not result['status_updated']:
            app.logger.error('Failed to approve case {}'.format(case_id))
            return jsonify(result), 500

        user_details = service.get_pending_by_id(case_id)

        insert_metric_event('dst action approved', user_details)

        return jsonify(result), 200

    except ApplicationError as error:
        error_msg = 'Failed to approve case - {}'.format(error.message)
        app.logger.error(error_msg)

        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/case/<case_id>/decline', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def decline_case(case_id):
    try:
        decline = request.get_json(force=True)
        app.logger.info("Declining case {}, by: {}".format(case_id, decline['staff_id']))
        result = service.dps_action('Decline', case_id, decline)
        if not result['status_updated']:
            app.logger.error('Failed to approve case {}'.format(case_id))
            return jsonify(result), 500

        user_details = service.get_pending_by_id(case_id)
        user_details['decline_reason'] = decline['reason']

        return jsonify(result), 200

    except ApplicationError as error:
        error_msg = 'Failed to decline case - {}'.format(error.message)
        app.logger.error(error_msg)

        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/case/<case_id>/note', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def insert_notes(case_id):
    try:
        note_details = request.get_json(force=True)
        app.logger.info("Inserting note for case {}".format(case_id))
        service.insert_note(case_id, note_details)
        message = 'Note added for case {}'.format(case_id)
        return jsonify(message=message), 201
    except ApplicationError as error:
        error_msg = 'Failed to insert note - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/decline-reasons', methods=['GET'])
@produces('application/json')
def get_decline_reasons():
    try:
        app.logger.info('Fetching DPS decline reasons')
        reasons = service.get_decline_reasons()
        return jsonify(reasons)
    except ApplicationError as error:
        error_msg = 'Failed to get decline reasons - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/case/<case_id>/lock', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def lock_application(case_id):
    try:
        details = request.get_json(force=True)
        owner = details['staff_id']
        app.logger.info('Locking case {} to {}'.format(case_id, owner))
        service.manage_case_lock(case_id, owner)
        return '', 204
    except ApplicationError as error:
        app.logger.error('Failed to lock case - {}'.format(error.message))
        return jsonify(error=error.message), error.http_code
    except KeyError as error:
        app.logger.error('Bad request - staff_id not in body'.format(error))
        return jsonify(error="Failed to lock case - no 'staff_id' provided".format(error)), 400


@verification_bp.route('/case/<case_id>/unlock', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def unlock_application(case_id):
    try:
        app.logger.info('Unlocking case {}'.format(case_id))
        service.manage_case_lock(case_id)
        return '', 204
    except ApplicationError as error:
        app.logger.error('Failed to unlock case - {}'.format(error.message))
        return jsonify(error=error.message), error.http_code


@verification_bp.route('/case/<case_id>/close', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def close_account(case_id):
    try:
        closure_data = request.get_json(force=True)
        app.logger.info("Starting to close account {}".format(case_id))
        result = service.close_account(case_id, closure_data)
        closure_text = 'Account closure requested by: {}, for reason: {}'.format(closure_data['requester'],
                                                                                 closure_data['close_detail'])
        service.insert_note(case_id, {'staff_id': closure_data['staff_id'],
                                      'note_text': closure_text})

        user_details = service.get_pending_by_id(case_id)
        user_details = {key: '' if value is None else value for (key, value) in user_details.items()}
        closure_details = service.get_closure_by_id(case_id)
        user_details.update(closure_details)

        insert_metric_event('account closed', user_details)

        return jsonify(result), 200
    except ApplicationError as error:
        error_msg = 'Failed to close account {} - {}'.format(case_id, error.message)
        app.logger.error(error_msg)

        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/case/<ldap_id>/auto_close', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def auto_close(ldap_id):
    try:
        auto_close_data = request.get_json(force=True)
        app.logger.info("Starting to auto close account for ldap_id: {}".format(ldap_id))
        result = service.auto_close(ldap_id, auto_close_data)
        return jsonify(result), 200
    except ApplicationError as error:
        error_msg = 'Failed to auto close account for ldap_id: {} - {}'.format(ldap_id, error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/case/<case_id>/update', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def update_details(case_id):
    try:
        app.logger.info("Updating the contact preference for user {}".format(case_id))
        data = request.get_json(force=True)
        result = service.update_user_details(case_id, data)

        return jsonify(result), 200
    except ApplicationError as error:
        error_msg = 'Failed to update contact details - {}'.format(error.message)
        app.logger.error(error_msg)

        return jsonify(error=error_msg), error.http_code


@verification_bp.route('/case/<case_id>/update_dataset_access', methods=['POST'])
@consumes('application/json')
@produces('application/json')
def update_dataset_access(case_id):
    try:
        app.logger.info("Updating dataset access for case: {}".format(case_id))
        data = request.get_json(force=True)
        result = service.update_dataset_access(case_id, data)
        handle_dataset_access_metrics(service.get_pending_by_id(case_id), result)

        return jsonify(result), 200
    except ApplicationError as error:
        error_msg = 'Failed to update groups - {}'.format(error.message)

        return jsonify(error=error_msg), error.http_code


@verification_bp.route("/search", methods=['POST'])
@consumes('application/json')
@produces('application/json')
def search():
    try:
        app.logger.info("Performing a search")
        search_params = request.get_json(force=True)
        result = service.perform_search(search_params)
        return jsonify(result), 200
    except ApplicationError as error:
        error_msg = 'Failed to perform search - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route("/dataset-list-details", methods=['GET'])
@produces('application/json')
def get_dataset_list_details():
    try:
        app.logger.info("Getting detailed dataset list from ckan")
        dataset_list = service.get_dataset_list_details()
        return jsonify(dataset_list), 200
    except ApplicationError as error:
        error_msg = 'Failed to get detailed dataset list - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route("/groups/<case_id>", methods=['GET'])
@produces('application/json')
def get_groups(case_id):
    try:
        app.logger.info("Getting list of groups for {}".format(case_id))
        groups, _ = service.get_groups(case_id)
        return jsonify(groups), 200
    except ApplicationError as error:
        error_msg = 'Failed to get groups - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route("/dataset-activity/<case_id>", methods=['GET'])
@produces('application/json')
def get_users_dataset_activity(case_id):
    try:
        app.logger.info("Getting user's dataset_activity for {}".format(case_id))
        dataset_activity = service.get_dataset_activity(case_id)
        return jsonify(dataset_activity), 200
    except ApplicationError as error:
        error_msg = 'Failed to get dataset activity - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code


@verification_bp.route("/dataset-access/<case_id>", methods=['GET'])
@produces('application/json')
def get_user_dataset_access(case_id):
    try:
        app.logger.info("Getting user's access for {}".format(case_id))
        dataset_access = service.get_user_dataset_access(case_id)
        return jsonify(dataset_access), 200
    except ApplicationError as error:
        error_msg = 'Failed to get dataset access - {}'.format(error.message)
        app.logger.error(error_msg)
        return jsonify(error=error_msg), error.http_code
