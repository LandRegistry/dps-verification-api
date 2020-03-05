import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from common_utilities import errors

from verification_api.models import Case, Note, DeclineReason, Close
from verification_api.exceptions import ApplicationError
from verification_api.extensions import db
from verification_api.dependencies.account_api import AccountAPI
from verification_api.dependencies.ulapd_api import UlapdAPI


log = logging.getLogger(__name__)


def handle_errors(is_get):
    def wrapper(func):
        def run_and_handle(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as error:
                log.error(str(error))
                error_code = 500 if is_get else 422
                error_def = errors.get('verification_api', 'SQLALCHEMY_ERROR', filler=str(error))
                raise ApplicationError(*error_def, http_code=error_code)
            except ApplicationError as error:
                raise error
            finally:
                if not is_get:
                    db.session.rollback()
                db.session.close()
        return run_and_handle
    return wrapper


@handle_errors(is_get=True)
def get_pending():
    return _extract_rows(Case.get_pending())


@handle_errors(is_get=True)
def get_pending_by_id(case_id):
    case = Case.get_case_by_id(case_id)
    if case:
        result = case.as_dict()
        notes = Note.get_notepad_by_case_id(case_id)
        result['notes'] = _extract_rows(notes)
    else:
        log.error("Case '{}' not found".format(case_id))
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    return result


@handle_errors(is_get=False)
def dps_action(action, case_id, data):
    case = Case.get_case_by_id(case_id)
    if not case:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    if not _can_perform_action(case, data['staff_id']):
        error_msg = 'Could not perform action on case as it is locked to another user'
        raise ApplicationError(*errors.get('verification_api', 'LOCKING_ERROR', filler=error_msg), http_code=403)

    account_api = AccountAPI()

    if action == 'Approve':
        account_api.approve(case.ldap_id)
        _status_update(case, 'Approved', data)
    elif action == 'Decline':
        # need to make the first letter in the reason lowercase due to the layout of the template
        reason = data['reason'][0].lower() + data['reason'][1:]
        account_api.decline(case.ldap_id, reason, data['advice'], case.user_id)
        _status_update(case, 'Declined', data)
        # add the decline reason as a notepad entry
        note_text = 'Declined: Reason - {}; Next Steps - {}'.format(data['reason'], data['advice'])
        _add_note(case_id, data['staff_id'], note_text)

    else:
        error_msg = 'Invalid action {}'.format(action)
        log.error(error_msg)
        raise ApplicationError(*errors.get('verification_api', 'VERIFICATION_ERROR', filler=str(error_msg)),
                               http_code=500)

    data['status_updated'] = True
    data['case_id'] = case_id
    db.session.commit()

    return data


@handle_errors(is_get=False)
def close_account(case_id, data):
    case = Case.get_case_by_id(case_id)
    if not case:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    if case.status != 'Approved':
        error_msg = 'Account closure only permitted on active user accounts'
        log.error(error_msg)
        error = errors.get('verification_api', 'VERIFICATION_ERROR', filler=str(error_msg))
        raise ApplicationError(*error, http_code=409)

    account_api = AccountAPI()
    account_api.close(case.ldap_id, case.user_id, data['requester'])

    closure = Close(case_id, data)
    db.session.add(closure)

    case.status = 'Closed'
    db.session.commit()
    data['status_updated'] = True
    data['case_id'] = case_id
    return data


@handle_errors(is_get=False)
def auto_close(ldap_id, close_data):
    case = Case.get_case_by_ldap_id(ldap_id)

    # Actually mark as closed if eligible for closure
    if close_data['close']:
        case.status = 'Closed'
        close_data['requester'] = 'HMLR'
        close_data['close_detail'] = 'Automated account closure'
        closure = Close(case.verification_id, close_data)
        db.session.add(closure)

    # Always add note for warning/close
    insert_note(case.verification_id, close_data)

    return {'status': True}


@handle_errors(is_get=True)
def get_closure_by_id(case_id):
    case = Close.get_closure_by_case_id(case_id)
    if not case:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)
    closure = {
        'closure_reason': case.close_detail,
        'date_closed': str(case.date_added)
    }
    return closure


@handle_errors(is_get=False)
def insert_case(case_details):
    user = Case(case_details)
    db.session.add(user)
    db.session.commit()
    return user.verification_id


@handle_errors(is_get=False)
def insert_note(case_id, note_data):
    case = Case.get_case_by_id(case_id)
    if case is None:
        log.error("Could not add note for case '{}' as it does not exist".format(case_id))
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    if _can_perform_action(case, note_data['staff_id']):
        _add_note(case_id, note_data['staff_id'], note_data['note_text'])
    else:
        error_msg = 'Could not add note to case as it is locked to another user'
        log.error(error_msg)
        raise ApplicationError(*errors.get('verification_api', 'LOCKING_ERROR', filler=error_msg), http_code=403)


@handle_errors(is_get=True)
def get_decline_reasons():
    decline = _extract_rows(DeclineReason.get_all_decline_reasons())
    reasons = []
    for row in decline:
        decline_dict = {
            'decline_reason': row['decline_description'],
            'decline_text': row['decline_detail'],
            'decline_advice': row['decline_advice']
        }
        reasons.append(decline_dict)

    return reasons


# Sets a lock on the specified case for the specified user.
# If no user is supplied, the case is unlocked instead.
@handle_errors(is_get=False)
def manage_case_lock(case_id, owner=None):
    case = Case.get_case_by_id(case_id)
    if case is None:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    if case.status in ['Approved', 'Declined']:
        error_msg = 'Cannot lock resolved case'
        raise ApplicationError(*errors.get('verification_api', 'LOCKING_ERROR', filler=error_msg))
    case.staff_id = owner
    db.session.commit()


@handle_errors(is_get=True)
def perform_search(search_params):
    first_name = search_params.get('first_name', '')
    last_name = search_params.get('last_name', '')
    organisation_name = search_params.get('organisation_name', '')
    email = search_params.get('email', '')
    return _extract_rows(Case.search(first_name, last_name, organisation_name, email))


@handle_errors(is_get=False)
def update_user_details(case_id, data):
    case = Case.get_case_by_id(case_id)
    if case is None:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    # update preference in ulapd
    ulapd = UlapdAPI()
    ulapd_data = {'user_id': case.user_id}
    for key, value in data['updated_data'].items():
        ulapd_data[key] = value
    ulapd.update(ulapd_data)

    case.registration_data = _update_registration_data(dict(case.registration_data), data['updated_data'])

    if 'contactable' in data['updated_data']:
        _add_update_note(case_id, data)

    db.session.commit()

    return {'updated': True}


@handle_errors(is_get=True)
def get_dataset_list_details():
    ulapd = UlapdAPI()
    dataset_list = ulapd.get_dataset_list_details()
    return dataset_list


@handle_errors(is_get=False)
def update_dataset_access(case_id, updated_access):
    case = Case.get_case_by_id(case_id)

    if case is None:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    data_dict = {
        'user_details_id': case.user_id,
        'licences': updated_access['licences']
    }

    ulapd_api = UlapdAPI()
    ulapd_api.update_dataset_access(data_dict)

    dataset_msgs = []
    for licence in updated_access['licences']:
        access_type = 'granted' if licence['agreed'] else 'removed'
        access_msg = 'access {} for {} dataset'.format(access_type, licence['licence_id'])
        dataset_msgs.append(access_msg)

    note_text = 'Data access updated: {}'.format(', '.join(dataset_msgs))
    _add_note(case_id, updated_access['staff_id'], note_text)

    return data_dict


@handle_errors(is_get=True)
def get_groups(case_id):
    log.info("Getting list of groups from account_api")
    case = Case.get_case_by_id(case_id)

    if case is None:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    ldap_details = AccountAPI().get(case.ldap_id)

    if isinstance(ldap_details['groups'], str):
        group_dns = [ldap_details['groups']]
    else:
        group_dns = ldap_details['groups']

    groups = [group.split(',')[0][3:] for group in group_dns]
    return groups, case


@handle_errors(is_get=True)
def get_dataset_activity(case_id):
    log.info('Getting dataset activity for {}'.format(case_id))
    case = Case.get_case_by_id(case_id)
    if case is None:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    ulapd = UlapdAPI()
    dataset_activities = ulapd.get_dataset_activity(case.user_id)

    return dataset_activities


@handle_errors(is_get=True)
def get_user_dataset_access(case_id):
    log.info('Getting dataset access for {}'.format(case_id))
    case = Case.get_case_by_id(case_id)
    if case is None:
        raise ApplicationError(*errors.get('verification_api', 'CASE_NOT_FOUND', filler=case_id), http_code=404)

    ulapd = UlapdAPI()
    dataset_access_list = ulapd.get_user_dataset_access(case.user_id)

    return dataset_access_list


def _extract_rows(rows):
    return [row.as_dict() for row in rows]


def _add_note(case_id, staff_id, note_text):
    entry = {
        'case_id': case_id,
        'staff_id': staff_id,
        'note_text': note_text
    }

    note = Note(entry)
    db.session.add(note)
    db.session.commit()


def _status_update(user, decision, data):
    user.status = decision
    user.staff_id = data['staff_id']
    user.date_agreed = datetime.utcnow()


def _can_perform_action(case, staff_id):
    if case.status == 'Pending':
        return staff_id == case.staff_id
    return True


def _update_registration_data(data, updated_data):
    for key, value in updated_data.items():
        data[key] = value
    return data


def _add_update_note(case_id, data):
    contacts = data['updated_data']['contact_preferences']
    if not data['updated_data']['contactable']:
        note = 'Contact Preference has been updated to No due to User request'
    else:
        if len(contacts) == 1:
            note = 'Contact Preference has been updated to {} due to User request'.format(contacts[0])
        else:
            start = ", ".join(contacts[:-1])
            contact_string = '{} and {}'.format(start, contacts[-1])

            note = 'Contact Preferences have been updated to {} due to User request'.format(contact_string)

    _add_note(case_id, data['staff_id'], note)


def _filter_groups_to_update(existing_groups, new_groups):
    # Create only list of group CNs
    user_groups = [x.split(',')[x.find('cn=')][3:] for x in existing_groups]

    groups_to_update = {}

    for key, value in new_groups.items():
        if (key in user_groups) != value:
            groups_to_update[key] = value

    return groups_to_update
