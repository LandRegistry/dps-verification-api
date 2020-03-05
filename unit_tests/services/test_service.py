import os
import json
import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import ProgrammingError
from common_utilities import errors

from verification_api.main import app
from verification_api.services import verification_service as service
from verification_api.exceptions import ApplicationError


@patch('verification_api.services.verification_service.db')
@patch('verification_api.services.verification_service.Case')
class TestService(unittest.TestCase):
    directory = os.path.dirname(__file__)
    decline_data = json.loads(open(os.path.join(directory, 'data/decline_reasons.json'), 'r').read())

    def setUp(self):
        self.app = app.test_client()
        self.error = ProgrammingError('stuff failed', 'Program', 'Error')
        self.dataset_activity = [
            {'private': True,
             'name': 'nps',
             'licence_agreed': True}
        ]

    @patch("verification_api.services.verification_service._extract_rows")
    def test_get_pending(self, mock_extract, mock_case, *_):
        pending = [{'foo': 'bar'}, {'foo': 'bar'}]
        mock_extract.return_value = pending
        mock_case.get_pending.return_value = _generate_test_profile()
        result = service.get_pending()
        self.assertEqual(result, pending)

    @patch("verification_api.services.verification_service._extract_rows")
    def test_get_pending_error(self, mock_extract, mock_case, *_):
        error = ('verification_api', 'VERIFICATION_ERROR')
        mock_extract.side_effect = ApplicationError(*errors.get(*error, filler='TEST ERR'))

        with self.assertRaises(ApplicationError) as context:
            mock_case.get_pending.return_value = _generate_test_profile()
            service.get_pending()

        self.assertEqual(context.exception.message, errors.get_message(*error, filler='TEST ERR'))
        self.assertEqual(context.exception.code, errors.get_code(*error))

    def test_get_pending_sql_error(self, mock_case, *_):
        with self.assertRaises(ApplicationError) as context:
            mock_case.get_pending.side_effect = self.error
            service.get_pending()

        self.assertEqual(context.exception.message, errors.get_message("verification_api", "SQLALCHEMY_ERROR",
                                                                       filler=self.error))
        self.assertEqual(errors.get_code("verification_api", "SQLALCHEMY_ERROR"), context.exception.code)

    @patch("verification_api.services.verification_service.Note.get_notepad_by_case_id")
    @patch("verification_api.services.verification_service._extract_rows")
    def test_get_pending_by_id(self, mock_extract, mock_note, mock_case, *_):
        mocked_case = MagicMock()
        mocked_case.as_dict.return_value = {'foo': 'bar'}
        mock_case.get_case_by_id.return_value = mocked_case
        mock_note.return_value = [{'my_note': 'A note'}]
        mock_extract.return_value = [{'my_note': 'A note'}]

        result = service.get_pending_by_id('1')
        self.assertEqual(result, {'foo': 'bar', 'notes': [{'my_note': 'A note'}]})

    def test_get_pending_by_id_no_row(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None
        with self.assertRaises(ApplicationError) as context:
            service.get_pending_by_id('1')

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    def test_get_pending_by_id_sql_error(self, mock_case, *_):
        with self.assertRaises(ApplicationError) as context:
            mock_case.get_case_by_id.side_effect = self.error
            service.get_pending_by_id('1')

        self.assertEqual(context.exception.message, errors.get_message("verification_api", "SQLALCHEMY_ERROR",
                                                                       filler=self.error))
        self.assertEqual(errors.get_code("verification_api", "SQLALCHEMY_ERROR"), context.exception.code)

    @patch("verification_api.services.verification_service.AccountAPI")
    @patch("verification_api.services.verification_service.Case.get_case_by_id")
    @patch("verification_api.services.verification_service._can_perform_action")
    def test_dps_action_approve(self, mock_lock, mock_case, *_):
        mock_lock.return_value = True
        mock_case.return_value = _generate_test_profile()
        data = {'staff_id': 'LRTM101'}

        result = service.dps_action('Approve', '1', data)

        expected_result = {
            'case_id': '1',
            'staff_id': 'LRTM101',
            'status_updated': True
        }
        self.assertEqual(result, expected_result)

    @patch("verification_api.services.verification_service.AccountAPI")
    @patch("verification_api.services.verification_service.Case.get_case_by_id")
    @patch("verification_api.services.verification_service._can_perform_action")
    def test_dps_action_approve_locked(self, mock_lock, mock_case, *_):
        mock_lock.return_value = False
        mock_case.return_value = _generate_test_profile()
        data = {'staff_id': 'LRTM101'}
        with self.assertRaises(ApplicationError) as context:
            service.dps_action('Approve', '1', data)

        expected_err = ('verification_api', 'LOCKING_ERROR')
        expected_err_message = 'Could not perform action on case as it is locked to another user'
        expected_err_message = errors.get_message(*expected_err, filler=expected_err_message)
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service.AccountAPI")
    @patch("verification_api.services.verification_service.Case.get_case_by_id")
    @patch("verification_api.services.verification_service._can_perform_action")
    def test_dps_action_decline(self, mock_lock, mock_case, *_):
        mock_lock.return_value = True
        mock_case.return_value = _generate_test_profile()
        data = {'staff_id': 'LRTM101', 'reason': 'Company Failed', 'advice': 'Reapply'}

        result = service.dps_action('Decline', '1', data)

        expected_result = {
            'case_id': '1',
            'staff_id': 'LRTM101',
            'reason': 'Company Failed',
            'advice': 'Reapply',
            'status_updated': True
        }
        self.assertDictEqual(result, expected_result)

    @patch("verification_api.services.verification_service.AccountAPI")
    @patch("verification_api.services.verification_service.Case.get_case_by_id")
    @patch("verification_api.services.verification_service._can_perform_action")
    def test_dps_action_invalid_action(self, mock_lock, mock_case, *_):
        mock_lock.return_value = True
        mock_case.return_value = _generate_test_profile()
        data = {'staff_id': 'LRTM101', 'reason': 'Company Failed'}

        with self.assertRaises(ApplicationError) as context:
            service.dps_action('Obliviate', '1', data)

        expected_err = ('verification_api', 'VERIFICATION_ERROR')
        expected_err_message = errors.get_message(*expected_err, filler='Invalid action Obliviate')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service._add_note")
    @patch("verification_api.services.verification_service.AccountAPI")
    @patch("verification_api.services.verification_service.Case.get_case_by_id")
    @patch("verification_api.services.verification_service._status_update")
    @patch("verification_api.services.verification_service._can_perform_action")
    def test_dps_action_decline_locked(self, mock_lock, mock_status, mock_case, *_):
        mock_status.return_value = True
        mock_lock.return_value = False
        mock_case.return_value = _generate_test_profile()
        data = {'staff_id': 'LRTM101', 'reason': 'Company Failed', 'advice': 'Reapply'}

        with self.assertRaises(ApplicationError) as context:
            service.dps_action('Decline', '1', data)

        expected_err = ('verification_api', 'LOCKING_ERROR')
        expected_err_message = 'Could not perform action on case as it is locked to another user'
        expected_err_message = errors.get_message(*expected_err, filler=expected_err_message)
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service.AccountAPI")
    def test_close(self, __, mock_case, *_):
        mock_case.get_case_by_id.return_value = _generate_test_profile(status='Approved')
        data = {
            'staff_id': 'AA111ZZ',
            'close_detail': 'Test closure reason',
            'requester': 'hmlr'
        }

        result = service.close_account('1', data)

        expected_result = {
            'staff_id': 'AA111ZZ',
            'close_detail': 'Test closure reason',
            'requester': 'hmlr',
            'case_id': '1',
            'status_updated': True
        }
        self.assertDictEqual(result, expected_result)

    def test_close_account_case_not_found(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None
        with self.assertRaises(ApplicationError) as context:
            service.close_account('1', {})

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    def test_close_account_invalid_status(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = _generate_test_profile(status='Pending')
        with self.assertRaises(ApplicationError) as context:
            service.close_account('1', {})

        expected_err = ('verification_api', 'VERIFICATION_ERROR')
        expected_err_message = 'Account closure only permitted on active user accounts'
        expected_err_message = errors.get_message(*expected_err, filler=expected_err_message)
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service.insert_note")
    @patch("verification_api.services.verification_service.Close")
    def test_auto_close(self, mock_closure, mock_insert_note, mock_case, mock_db):
        mock_case.get_case_by_ldap_id.return_value = _generate_test_profile(status='Approved')

        close_data = {
            'close': True,
            'staff_id': 'Test ID',
            'note_text': 'hello world'
        }

        service.auto_close('123', close_data)

        mock_closure.assert_called_once()
        mock_insert_note.assert_called_once_with(233, close_data)

    @patch("verification_api.services.verification_service.insert_note")
    @patch("verification_api.services.verification_service.Close")
    def test_auto_close_without_closing_account(self, mock_closure, mock_insert_note, mock_case, mock_db):
        mock_case.get_case_by_ldap_id.return_value = _generate_test_profile(status='Approved')

        close_data = {
            'close': False,
            'staff_id': 'Test ID',
            'note_text': 'hello world'
        }

        service.auto_close('123', close_data)
        mock_closure.assert_not_called()
        mock_insert_note.assert_called_once_with(233, close_data)

    def test_dps_action_no_row(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None

        with self.assertRaises(ApplicationError) as context:
            service.dps_action('Approve', '1', {'staff_id': 'LRTM101'})

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service.AccountAPI")
    def test_dps_action_error(self, mock_account, mock_case, *_):
        error = ('verification_api', 'VERIFICATION_ERROR')
        mock_account.side_effect = ApplicationError(*errors.get(*error, filler='TEST ERROR'))
        mock_case.get_case_by_id.return_value = _generate_test_profile()

        with self.assertRaises(ApplicationError) as context:
            service.dps_action('Approve', '1', {'staff_id': 'LRTM101'})

        expected_err = errors.get_message(*error, filler='TEST ERROR')
        self.assertEqual(context.exception.message, expected_err)
        self.assertEqual(context.exception.code, errors.get_code(*error))

    def test_dps_action_sql_error(self, mock_case, *_):
        with self.assertRaises(ApplicationError) as context:
            mock_case.get_case_by_id.side_effect = self.error
            service.dps_action('Approve', '1', {'staff_id': 'LRTM101'})

        self.assertEqual(context.exception.message, errors.get_message("verification_api", "SQLALCHEMY_ERROR",
                                                                       filler=self.error))
        self.assertEqual(errors.get_code("verification_api", "SQLALCHEMY_ERROR"), context.exception.code)

    def test_insert_case(self, mock_case, *_):
        mock_case.return_value = _generate_test_profile()
        result = service.insert_case({'foo': 'bar'})
        self.assertEqual(result, mock_case.return_value.verification_id)

    def test_insert_case_error(self, mock_case, *_):
        error = ('verification_api', 'VERIFICATION_ERROR')
        mock_case.side_effect = ApplicationError(*errors.get(*error, filler='TEST ERR'))
        with self.assertRaises(ApplicationError) as context:
            service.insert_case({'foo': 'bar'})

        self.assertEqual(context.exception.message, errors.get_message(*error, filler='TEST ERR'))
        self.assertEqual(context.exception.code, errors.get_code(*error))

    def test_insert_case_sql_error(self, mock_case, *_):
        with self.assertRaises(ApplicationError) as context:
            mock_case.side_effect = self.error
            service.insert_case({'foo': 'bar'})

        self.assertEqual(context.exception.message, errors.get_message("verification_api", "SQLALCHEMY_ERROR",
                                                                       filler=self.error))
        self.assertEqual(errors.get_code("verification_api", "SQLALCHEMY_ERROR"), context.exception.code)

    def test_add_note_case_not_found(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None

        with self.assertRaises(ApplicationError) as context:
            service.insert_note('1', {})

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service._can_perform_action")
    def test_add_note_case_locked(self, mock_lock, mock_case, *_):
        mock_lock.return_value = False
        mock_case.get_case_by_id.return_value = _generate_test_profile()
        test_note = {'staff_id': 'SOMEONE_ELSE'}

        with self.assertRaises(ApplicationError) as context:
            service.insert_note('1', test_note)

        expected_err = ('verification_api', 'LOCKING_ERROR')
        expected_err_message = 'Could not add note to case as it is locked to another user'
        expected_err_message = errors.get_message(*expected_err, filler=expected_err_message)
        expected_err_code = errors.get_code(*expected_err)

        mock_lock.assert_called_once()
        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service._add_note")
    @patch("verification_api.services.verification_service._can_perform_action")
    def test_insert_note(self, mock_lock, mock_note, mock_case, *_):
        mock_case.get_case_by_id.return_value = MagicMock()
        mock_lock.return_value = True
        service.insert_note('1', {'staff_id': 'LRTM101', 'note_text': 'Test note'})
        mock_note.assert_called_once_with('1', 'LRTM101', 'Test note')
        mock_case.get_case_by_id.assert_called_once()

    @patch("verification_api.services.verification_service._can_perform_action")
    def test_insert_note_error(self, mock_lock, *_):
        test_error = ('verification_api', 'VERIFICATION_ERROR')
        mock_lock.side_effect = ApplicationError(*errors.get(*test_error, filler='TEST ERROR'))

        with self.assertRaises(ApplicationError) as context:
            service.insert_note('1', {'staff_id': 'LRTM101', 'note_text': 'Test note'})

        expected_err_message = errors.get_message(*test_error, filler='TEST ERROR')
        expected_err_code = errors.get_code(*test_error)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    def test_insert_note_sql_error(self, mock_case, *_):
        mock_case.get_case_by_id.side_effect = self.error
        with self.assertRaises(ApplicationError) as context:
            service.insert_note('1', {})

        expected_err = ('verification_api', 'SQLALCHEMY_ERROR')
        self.assertEqual(context.exception.message, errors.get_message(*expected_err, filler=self.error))
        self.assertEqual(context.exception.code, errors.get_code(*expected_err))

    @patch("verification_api.services.verification_service.DeclineReason.get_all_decline_reasons")
    @patch("verification_api.services.verification_service._extract_rows")
    def test_decline_reasons(self, mock_extract, *_):
        mock_extract.return_value = self.decline_data
        result = service.get_decline_reasons()
        assert 'decline_reason' in result[0]
        assert 'decline_text' in result[0]
        assert 'decline_advice' in result[0]
        assert 'decline_id' not in result[0]

    @patch("verification_api.services.verification_service.DeclineReason.get_all_decline_reasons")
    @patch("verification_api.services.verification_service._extract_rows")
    def test_decline_reasons_error(self, mock_extract, *_):
        error = ('verification_api', 'VERIFICATION_ERROR')
        mock_extract.side_effect = ApplicationError(*errors.get(*error, filler='TEST ERR'))

        with self.assertRaises(ApplicationError) as context:
            service.get_decline_reasons()

        self.assertEqual(context.exception.message, errors.get_message(*error, filler='TEST ERR'))
        self.assertEqual(context.exception.code, errors.get_code(*error))

    @patch("verification_api.services.verification_service._extract_rows")
    @patch("verification_api.services.verification_service.DeclineReason.get_all_decline_reasons")
    def test_decline_reasons_sql_error(self, mock_decline, mock_extract, *_):
        with self.assertRaises(ApplicationError) as context:
            mock_extract.return_value = self.decline_data
            mock_decline.side_effect = self.error
            service.get_decline_reasons()

        self.assertEqual(context.exception.message, errors.get_message("verification_api", "SQLALCHEMY_ERROR",
                                                                       filler=self.error))
        self.assertEqual(errors.get_code("verification_api", "SQLALCHEMY_ERROR"), context.exception.code)

    def test_manage_case_lock(self, mock_case, mock_db):
        test_staff_id = 'LRTM101'
        mocked_case = MagicMock()
        mocked_case.status = 'In Progress'
        mock_case.get_case_by_id.return_value = mocked_case

        service.manage_case_lock('1', test_staff_id)

        mock_db.session.commit.assert_called_once()
        self.assertEqual(test_staff_id, mocked_case.staff_id)

    def test_manage_case_lock_case_not_found(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None
        test_case_id = '1'
        with self.assertRaises(ApplicationError) as context:
            service.manage_case_lock(test_case_id)

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    def test_manage_case_lock_invalid_status(self, mock_case, *_):
        mocked_case = MagicMock()
        mocked_case.status = 'Approved'
        mock_case.get_case_by_id.return_value = mocked_case

        test_case_id = '1'
        with self.assertRaises(ApplicationError) as context:
            service.manage_case_lock(test_case_id)

        expected_err = ('verification_api', 'LOCKING_ERROR')
        expected_err_message = errors.get_message(*expected_err, filler='Cannot lock resolved case')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    def test_manage_case_lock_sql_error(self, mock_case, *_):
        mock_case.get_case_by_id.side_effect = self.error

        with self.assertRaises(ApplicationError) as context:
            service.manage_case_lock('1')

        expected_err = ('verification_api', 'SQLALCHEMY_ERROR')
        expected_err_message = errors.get_message(*expected_err, filler=self.error)
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service._extract_rows")
    def test_perform_search(self, mock_extract_rows, mock_case, *_):
        search_result = [{'foo': 'bar'}, {'foo': 'bar'}]
        mock_case.search.return_value = _generate_test_profile()
        mock_extract_rows.return_value = search_result
        search_params = {
            "first_name": "Andreea",
            "last_name": "",
            "organisation_name": "",
            "email": "",
        }
        result = service.perform_search(search_params)
        self.assertEqual(result, search_result)
        mock_case.search.assert_called_once()
        mock_extract_rows.assert_called_once()

    @patch("verification_api.services.verification_service._extract_rows")
    def test_perform_search_error(self, mock_extract_rows, mock_case, *_):
        search_params = {
            "first_name": "Andreea",
            "last_name": "",
            "organisation_name": "",
            "email": "",
        }
        test_error = ('verification_api', 'VERIFICATION_ERROR')
        mock_extract_rows.side_effect = ApplicationError(*errors.get(*test_error, filler='TEST ERROR'))

        with self.assertRaises(ApplicationError) as context:
            service.perform_search(search_params)

        expected_error_msg = errors.get_message(*test_error, filler='TEST ERROR')
        expected_error_code = errors.get_code(*test_error)
        self.assertEqual(context.exception.message, expected_error_msg)
        self.assertEqual(context.exception.code, expected_error_code)
        mock_case.search.assert_called_once()
        mock_extract_rows.assert_called_once()

    @patch("verification_api.services.verification_service._extract_rows")
    def test_perform_search_sql_error(self, mock_extract_rows, mock_case, *_):
        search_result = [{'foo': 'bar'}, {'foo': 'bar'}]
        search_params = {
            "first_name": "Andreea",
            "last_name": "",
            "organisation_name": "",
            "email": "",
        }
        mock_extract_rows.return_value = search_result
        mock_case.search.side_effect = self.error

        with self.assertRaises(ApplicationError) as context:
            service.perform_search(search_params)

        expected_err = ('verification_api', 'SQLALCHEMY_ERROR')
        expected_err_message = errors.get_message(*expected_err, filler=self.error)
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)
        mock_case.search.assert_called_once()
        mock_extract_rows.assert_not_called()

    @patch("verification_api.services.verification_service.Close.get_closure_by_case_id")
    def test_get_closure_by_id(self, mock_closure, *_):
        mock_closure.return_value = _generate_closure()

        result = service.get_closure_by_id('1')
        self.assertEqual(result, {'closure_reason': 'test closure', 'date_closed': '2019-01-01'})

    @patch("verification_api.services.verification_service.Close")
    def test_get_closure_by_id_no_row(self, mock_closure, *_):
        mock_closure.get_closure_by_case_id.return_value = None
        with self.assertRaises(ApplicationError) as context:
            service.get_closure_by_id('1')

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service.Close.get_closure_by_case_id")
    def test_get_closure_by_id_sql_error(self, mock_closure, *_):
        with self.assertRaises(ApplicationError) as context:
            mock_closure.side_effect = self.error
            service.get_closure_by_id('1')

        self.assertEqual(context.exception.message, errors.get_message("verification_api", "SQLALCHEMY_ERROR",
                                                                       filler=self.error))
        self.assertEqual(errors.get_code("verification_api", "SQLALCHEMY_ERROR"), context.exception.code)

    @patch("verification_api.services.verification_service.Case.get_case_by_id")
    @patch("verification_api.services.verification_service._update_registration_data")
    @patch("verification_api.services.verification_service._add_update_note")
    @patch("verification_api.services.verification_service.UlapdAPI")
    def test_update_user_details(self, mock_ulapd, mock_note, mock_update_reg, mock_case, *_):
        mock_case.return_value = _generate_test_profile()
        mock_update_reg.return_value = {'foo': 'bar'}
        mock_ulapd.update.return_value = {'message': 'user updated'}

        result = service.update_user_details(233, {'updated_data': {'contactable': True}, 'staff_id': 'test_user'})

        self.assertEqual(result, {'updated': True})
        mock_note.assert_called_once()

    def test_update_user_details_no_row(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None

        with self.assertRaises(ApplicationError) as context:
            service.update_user_details(1, {'foo': 'bar'})

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    def test_update_user_details_sql_error(self, mock_case, *_):
        with self.assertRaises(ApplicationError) as context:
            mock_case.get_case_by_id.side_effect = self.error
            service.update_user_details(1, {'foo': 'bar'})

        self.assertEqual(context.exception.message, errors.get_message("verification_api", "SQLALCHEMY_ERROR",
                                                                       filler=self.error))
        self.assertEqual(errors.get_code("verification_api", "SQLALCHEMY_ERROR"), context.exception.code)

    @patch("verification_api.services.verification_service.UlapdAPI")
    def test_get_dataset_list_details(self, mock_ulapd_api, *_):
        mock_ulapd_api.return_value.get_dataset_list_details.return_value = [
            {
                "id": "12345", "name": "test",
                "title": "Test Dataset", "private": True
            }
        ]

        dataset_list = service.get_dataset_list_details()

        mock_ulapd_api.assert_called_once()
        self.assertEqual(dataset_list, [{"id": "12345", "name": "test", "title": "Test Dataset", "private": True}])

    @patch("verification_api.services.verification_service._add_note")
    @patch("verification_api.services.verification_service.UlapdAPI")
    def test_update_dataset_access(self, mock_ulapd_api, mock_add_note, mock_case, *_):
        mock_case.get_case_by_id.return_value = MagicMock(user_id=123)

        updated_access = {
            'staff_id': 'CS999xx',
            'licences': [
                {
                    'licence_id': 'nps',
                    'agreed': True
                },
                {
                    'licence_id': 'dad',
                    'agreed': False
                }
            ]
        }

        result = service.update_dataset_access(666, updated_access)

        expected_result = {
            'user_details_id': 123,
            'licences': updated_access['licences']
        }

        self.assertEqual(result, expected_result)
        expected_note_text = 'Data access updated: access granted for nps dataset, access removed for dad dataset'
        mock_add_note.assert_called_with(666, 'CS999xx', expected_note_text)

    def test_update_dataset_access_no_row(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None

        with self.assertRaises(ApplicationError) as context:
            service.update_dataset_access(666, {})

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='666')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service.AccountAPI")
    @patch("verification_api.services.verification_service.Case")
    def test_get_groups_single(self, mock_case, mock_account_api, *_):
        case_id = 999
        mock_case_details = MagicMock()
        mock_case_details.ldap_id = '06a4da7e-adba-43f3-91fb-d86a34355a55'
        mock_case.return_value.get_case_by_id.return_value = mock_case_details
        mock_account_api.return_value.get.return_value = {'groups': 'cn=test,ou=groups,dc=HMLR,dc=zone'}

        groups, case = service.get_groups(case_id)

        mock_account_api.assert_called_once()
        self.assertEqual(groups, ['test'])

    @patch("verification_api.services.verification_service.AccountAPI")
    @patch("verification_api.services.verification_service.Case")
    def test_get_groups_multiple(self, mock_case, mock_account_api, *_):
        case_id = 999
        mock_case_details = MagicMock()
        mock_case_details.ldap_id = '06a4da7e-adba-43f3-91fb-d86a34355a55'
        mock_case.return_value.get_case_by_id.return_value = mock_case_details
        mock_account_api.return_value.get.return_value = {'groups': ['cn=test,ou=groups,dc=HMLR,dc=zone',
                                                                     'cn=pinkhaze,ou=groups,dc=HMLR,dc=zone']}

        groups, case = service.get_groups(case_id)

        mock_account_api.assert_called_once()
        self.assertEqual(groups, ['test', 'pinkhaze'])

    def test_get_groups_case_not_found(self, mock_case, *_):
        case_id = 999
        mock_case.get_case_by_id.return_value = None

        with self.assertRaises(ApplicationError) as context:
            service.get_groups(case_id)

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='999')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)

    @patch("verification_api.services.verification_service.UlapdAPI")
    def test_get_dataset_activity_ok(self, mock_ulapd, *_):
        case = MagicMock()
        case.user_id = '2'

        mock_ulapd.return_value.get_dataset_activity.return_value = self.dataset_activity

        result = service.get_dataset_activity(1)
        self.assertEqual(result[0]['licence_agreed'], True)

    @patch("verification_api.services.verification_service.UlapdAPI")
    def test_get_dataset_activity_ok_nps_not_granted(self, mock_ulapd, *_):
        case = MagicMock()
        case.user_id = '1'
        response = [{'private': True, 'name': 'nps', 'licence_agreed': False}]
        mock_ulapd.return_value.get_dataset_activity.return_value = response

        result = service.get_dataset_activity(1)
        self.assertEqual(result[0]['licence_agreed'], False)

    @patch("verification_api.services.verification_service.UlapdAPI")
    def test_get_dataset_activity_ok_multiple_datasets(self, mock_ulapd, *_):
        case = MagicMock()
        case.user_id = '3'
        dataset_activities = self.dataset_activity
        dataset_activities.append({'private': True,
                                   'name': 'leases',
                                   'licence_agreed': False})
        mock_ulapd.return_value.get_dataset_activity.return_value = self.dataset_activity

        result = service.get_dataset_activity(1)
        self.assertEqual(result[0]['licence_agreed'], True)
        self.assertEqual(result[1]['licence_agreed'], False)

    @patch("verification_api.services.verification_service.UlapdAPI")
    def test_get_user_dataset_access(self, mock_ulapd, mock_case, *_):
        mock_case.get_case_by_id.return_value = MagicMock(user_id=1)
        response = [
            {
                'name': 'res_cov',
                'licences': {
                    'res_cov_direct': {
                        'title': 'Direct Use',
                        'agreed': True
                    }
                }
            }
        ]

        mock_ulapd.return_value.get_user_dataset_access.return_value = response

        result = service.get_user_dataset_access(1)
        self.assertEqual(result[0]['licences']['res_cov_direct']['agreed'], True)
        mock_ulapd.return_value.get_user_dataset_access.assert_called_with(1)

    def test_get_user_dataset_access_no_row(self, mock_case, *_):
        mock_case.get_case_by_id.return_value = None

        with self.assertRaises(ApplicationError) as context:
            service.get_user_dataset_access(1)

        expected_err = ('verification_api', 'CASE_NOT_FOUND')
        expected_err_message = errors.get_message(*expected_err, filler='1')
        expected_err_code = errors.get_code(*expected_err)

        self.assertEqual(context.exception.message, expected_err_message)
        self.assertEqual(context.exception.code, expected_err_code)


class TestServicePrivateFunctions(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_extract_rows_no_rows(self):
        result = service._extract_rows([])
        self.assertEqual(result, [])

    def test_extract_rows(self):
        mock_row = MagicMock()
        mock_row.as_dict.return_value = {'foo': 'bar'}
        result = service._extract_rows([mock_row, mock_row])
        self.assertEqual(result, [{'foo': 'bar'}, {'foo': 'bar'}])

    def test_status_update_true(self):
        mock_user = MagicMock()
        test_data = {'verification_id': 123, 'staff_id': 'mr test'}
        service._status_update(mock_user, 'Approved', test_data)
        self.assertEqual(mock_user.status, 'Approved')
        self.assertEqual(mock_user.staff_id, test_data['staff_id'])

    @patch("verification_api.services.verification_service.db.session")
    @patch("verification_api.services.verification_service.Note")
    def test_add_note(self, mock_note, mock_db):
        test_case_id = '1'
        test_staff_id = 'LRTM101'
        test_text = 'TEST NOTE TEXT'
        mock_note_entry = MagicMock()
        mock_note.return_value = mock_note_entry

        service._add_note(test_case_id, test_staff_id, test_text)

        expected_dict_param = {
            'case_id': test_case_id,
            'staff_id': test_staff_id,
            'note_text': test_text
        }
        mock_note.assert_called_once_with(expected_dict_param)
        mock_db.add.assert_called_once_with(mock_note_entry)
        mock_db.commit.assert_called_once()

    def test_can_perform_action_status_not_applicable(self):
        mock_case = MagicMock()
        mock_case.status = 'Approved'

        result = service._can_perform_action(mock_case, MagicMock())
        self.assertTrue(result)

    def test_update_registration_data(self):
        reg_data = {
            'contactable': False,
            'postcode': 'PL1 1AA',
            'first_name': 'Ted'
        }
        updated_data = {
            'contactable': True,
            'postcode': 'PL2 2BB'
        }
        expected_data = {
            'contactable': True,
            'postcode': 'PL2 2BB',
            'first_name': 'Ted'
        }
        result = service._update_registration_data(reg_data, updated_data)
        self.assertEqual(result, expected_data)

    @patch("verification_api.services.verification_service._add_note")
    def test_add_update_note_true_single(self, mock_note):
        data = {
            'updated_data': {'contactable': True, 'contact_preferences': ['Telephone']},
            'staff_id': 'test_staff'
        }
        service._add_update_note(1, data)
        mock_note.assert_called_once_with(1, 'test_staff',
                                          'Contact Preference has been updated to Telephone due to User request')

    @patch("verification_api.services.verification_service._add_note")
    def test_add_update_note_true_multiple(self, mock_note):
        data = {
            'updated_data': {'contactable': True, 'contact_preferences': ['Telephone', 'Email', 'Text']},
            'staff_id': 'test_staff'
        }
        service._add_update_note(1, data)
        expected_note = 'Contact Preferences have been updated to Telephone, Email and Text due to User request'
        mock_note.assert_called_once_with(1, 'test_staff', expected_note)

    @patch("verification_api.services.verification_service._add_note")
    def test_add_update_note_false(self, mock_note):
        data = {
            'updated_data': {'contactable': False, 'contact_preferences': []},
            'staff_id': 'test_staff'
        }
        service._add_update_note(1, data)
        mock_note.assert_called_once_with(1, 'test_staff',
                                          'Contact Preference has been updated to No due to User request')

    def test_filter_groups_to_update(self):
        existing_groups = ["cn=leases,ou=groups,dc=HMLR,dc=zone", "cn=nps,ou=groups,dc=HMLR,dc=zone"]
        new_groups = {"nps": False, "leases": True}

        result = service._filter_groups_to_update(existing_groups, new_groups)

        self.assertEqual(result, {"nps": False})


def _generate_test_profile(verification_id=233, user_id=123, staff_id='LRTM101', _sa_instance_state=None,
                           date_added=None, date_agreed=None, status='Pending'):
    test_profile = MagicMock()
    test_profile.verification_id = verification_id
    test_profile.user_id = user_id
    test_profile.staff_id = staff_id
    test_profile._sa_instance_state = _sa_instance_state
    test_profile.date_added = date_added
    test_profile.date_agreed = date_agreed
    test_profile.status = status
    return test_profile


def _generate_closure(close_detail='test closure', date_added='2019-01-01'):
    test_closure = MagicMock()
    test_closure.close_detail = close_detail
    test_closure.date_added = date_added
    return test_closure
