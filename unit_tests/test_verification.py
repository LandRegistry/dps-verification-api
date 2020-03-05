import unittest
from verification_api.main import app
from verification_api.exceptions import ApplicationError
from unittest.mock import patch
from common_utilities import errors


@patch('verification_api.views.v1.verification.insert_metric_event')
@patch('verification_api.views.v1.verification.insert_cf_event')
@patch('verification_api.views.v1.verification.AuditAPI')
@patch('verification_api.views.v1.verification.service')
class TestVerification(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json'}
        self.approve_body = {"staff_id": "test staff"}
        self.decline_body = {"staff_id": "test staff", "reason": "Company failed"}
        self.close_body = {"staff_id": "test staff", "requester": "hmlr",
                           "close_detail": "A test reason for closing account"}
        self.return_true_body = {'case_id': 1, 'staff_id': 'test staff', 'status_updated': True}
        self.return_false_body = {'case_id': 1, 'staff_id': 'test staff', 'status_updated': False}
        self.test_error = ('verification_api', 'VERIFICATION_ERROR', 'TEST ERROR')

    def test_get_worklist(self, mock_service, *_):
        mock_service.get_pending.return_value = [{'foo': 'bar'}]

        response = self.app.get('/v1/worklist', headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, [{'foo': 'bar'}])

    def test_get_worklist_error(self, mock_service, *_):
        mock_service.get_pending.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        response = self.app.get('/v1/worklist', headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual("Failed to retrieve worklist - " + expected_err_msg, response_body['error'])

    def test_get_worklist_item_not_found(self, mock_service, *_):
        mock_service.get_pending_by_id.return_value = {}

        response = self.app.get('/v1/case/1', headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, {})

    def test_get_worklist_item(self, mock_service, *_):
        expected_result = {'foo': 'bar', 'notes': [{'my_note': 'A note'}]}
        mock_service.get_pending_by_id.return_value = expected_result

        response = self.app.get('/v1/case/1', headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, expected_result)

    def test_get_worklist_item_error(self, mock_service, *_):
        mock_service.get_pending_by_id.side_effect = ApplicationError(*errors.get(*self.test_error))
        test_id = 1

        response = self.app.get('/v1/case/{}'.format(test_id), headers=self.headers)
        response_body = response.get_json()

        expected_err_msg = errors.get_message(*self.test_error)
        expected_err_msg = "Failed to get case '{}' - {}".format(test_id, expected_err_msg)
        self.assertEqual(500, response.status_code)
        self.assertEqual(expected_err_msg, response_body['error'])

    def test_approve_ok(self, mock_service, *_):
        mock_service.dps_action.return_value = self.return_true_body
        mock_service.get_pending_by_id.return_value = {'foo': 'bar', 'notes': [{'my_note': 'A note'}]}
        response = self.app.post('/v1/case/1/approve', json=self.approve_body, headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, self.return_true_body)

    def test_approve_fail(self, mock_service, *_):
        mock_service.dps_action.return_value = self.return_false_body

        response = self.app.post('/v1/case/1/approve', json=self.approve_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, self.return_false_body)

    def test_approve_error(self, mock_service, *_):
        mock_service.dps_action.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        response = self.app.post('/v1/case/1/approve', json=self.approve_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual("Failed to approve case - " + expected_err_msg, response_body['error'])

    def test_decline_ok(self, mock_service, *_):
        mock_service.dps_action.return_value = self.return_true_body
        mock_service.get_pending_by_id.return_value = {'foo': 'bar', 'notes': [{'my_note': 'A note'}]}
        response = self.app.post('/v1/case/1/decline', json=self.decline_body, headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, self.return_true_body)

    def test_decline_fail(self, mock_service, *_):
        mock_service.dps_action.return_value = self.return_false_body

        response = self.app.post('/v1/case/1/decline', json=self.decline_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, self.return_false_body)

    def test_decline_error(self, mock_service, *_):
        mock_service.dps_action.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        response = self.app.post('/v1/case/1/decline', json=self.decline_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual("Failed to decline case - " + expected_err_msg, response_body['error'])

    def test_insert_case(self, mock_service, *_):
        mock_service.insert_case.return_value = 1

        json_body = {"registration_data": {"name": "tester"}, "user_id": "1213-12313-2313"}
        response = self.app.post('/v1/case', json=json_body, headers=self.headers)

        self.assertEqual(201, response.status_code)
        response_body = response.get_json()
        expected_body = {
            'message': 'user 1213-12313-2313 added to dps worklist',
            'case_id': 1
        }
        self.assertDictEqual(response_body, expected_body)

    def test_insert_case_error(self, mock_service, *_):
        mock_service.insert_case.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        json_body = {"registration_data": {"name": "tester"}, "user_id": "1213-12313-2313"}
        response = self.app.post('/v1/case', json=json_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual("Failed to insert case - " + expected_err_msg, response_body['error'])

    def test_notepad(self, *_):

        json_body = {'note_text': 'A note', 'staff_id': 'AA123ZZ'}
        response = self.app.post('/v1/case/1/note', json=json_body, headers=self.headers)

        self.assertEqual(201, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, {'message': 'Note added for case 1'})

    def test_notepad_error(self, mock_service, *_):
        mock_service.insert_note.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)
        json_body = {'note_text': 'A note', 'staff_id': 'AA123ZZ'}
        response = self.app.post('/v1/case/1/note', json=json_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual("Failed to insert note - " + expected_err_msg, response_body['error'])

    def test_decline_reasons(self, mock_service, *_):
        mock_service.get_decline_reasons.return_value = [
            {"decline_reason": "Company number invalid",
             "decline_text": "Following checks your company number is invalid"}
        ]
        response = self.app.get('/v1/decline-reasons', headers=self.headers)
        self.assertEqual(200, response.status_code)

    def test_decline_reason_error(self, mock_service, *_):
        mock_service.get_decline_reasons.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        response = self.app.get('/v1/decline-reasons', headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        self.assertEqual("Failed to get decline reasons - " + expected_err_msg, response_body['error'])

    def test_lock(self, mock_service, *_):
        json_body = {
            'staff_id': 'LRTM101'
        }

        response = self.app.post('/v1/case/1/lock', json=json_body, headers=self.headers)

        mock_service.manage_case_lock.assert_called_once_with('1', 'LRTM101')
        self.assertEqual(response.status_code, 204)

    def test_lock_bad_request(self, *_):
        response = self.app.post('/v1/case/1/lock', json={}, headers=self.headers)
        response_body = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_body['error'], "Failed to lock case - no 'staff_id' provided")

    def test_lock_error(self, mock_service, *_):
        mock_service.manage_case_lock.side_effect = ApplicationError(*errors.get(*self.test_error))
        json_body = {
            'staff_id': 'LRTM101'
        }

        response = self.app.post('/v1/case/1/lock', json=json_body, headers=self.headers)
        response_body = response.get_json()

        expected_error_msg = errors.get_message(*self.test_error)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_body['error'], expected_error_msg)

    def test_unlock(self, mock_service, *_):
        response = self.app.post('/v1/case/1/unlock', json={}, headers=self.headers)

        mock_service.manage_case_lock.assert_called_once_with('1')
        self.assertEqual(response.status_code, 204)

    def test_unlock_error(self, mock_service, *_):
        mock_service.manage_case_lock.side_effect = ApplicationError(*errors.get(*self.test_error))

        response = self.app.post('/v1/case/1/unlock', json={}, headers=self.headers)
        response_body = response.get_json()

        expected_error_msg = errors.get_message(*self.test_error)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_body['error'], expected_error_msg)

    def test_close_success(self, mock_service, mock_audit, *_):
        mock_service.close_account.return_value = self.return_true_body
        mock_service.get_closure_by_id.return_value = {'closure_reason': 'A closure reason',
                                                       'date_closed': '2018-09-09'}
        response = self.app.post('/v1/case/1/close', json=self.close_body, headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertEqual(response_body, self.return_true_body)
        mock_audit.assert_called_once()
        mock_service.close_account.assert_called_once()
        mock_service.insert_note.assert_called_once()
        closure_text = 'Account closure requested by: {}, for reason: {}'.format(self.close_body['requester'],
                                                                                 self.close_body['close_detail'])
        mock_service.insert_note.assert_called_with('1', {'staff_id': self.close_body['staff_id'],
                                                          'note_text': closure_text})

    def test_close_error(self, mock_service, mock_audit, *_):
        mock_service.close_account.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        response = self.app.post('/v1/case/1/close', json=self.close_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        mock_service.insert_note.assert_not_called()
        response_body = response.get_json()
        expected_err = 'Failed to close account 1 - {}'.format(expected_err_msg)
        self.assertEqual(expected_err, response_body['error'])

    def test_auto_close(self, mock_service, mock_audit, *_):
        mock_service.auto_close.return_value = {'status': True}

        response = self.app.post('/v1/case/123456/auto_close', json=self.close_body, headers=self.headers)

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.get_json(), {'status': True})

    def test_auto_close_error(self, mock_service, mock_audit, *_):
        mock_service.auto_close.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        response = self.app.post('/v1/case/123456/auto_close', json=self.close_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        expected_err = 'Failed to auto close account for ldap_id: 123456 - {}'.format(expected_err_msg)
        self.assertEqual(expected_err, response_body['error'])

    def test_search(self, mock_service, *_):
        mock_service.perform_search.return_value = [{'foo': 'bar'}]
        json_body = {"first_name": "Andreea"}
        response = self.app.post('/v1/search', json=json_body, headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertListEqual(response_body, [{'foo': 'bar'}])

    def test_search_error(self, mock_service, *_):
        mock_service.perform_search.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        json_body = {"first_name": "Andreea"}
        response = self.app.post('/v1/search', json=json_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        expected_err = 'Failed to perform search - {}'.format(expected_err_msg)
        self.assertEqual(expected_err, response_body['error'])

    def test_get_dataset_list_details(self, mock_service, *_):
        mock_service.get_dataset_list_details.return_value = [{"id": "12345", "name": "test",
                                                               "title": "Test Dataset", "private": True}]

        response = self.app.get('/v1/dataset-list-details', headers=self.headers)

        self.assertEqual(response.get_json(), [{"id": "12345", "name": "test",
                                                "title": "Test Dataset", "private": True}])
        self.assertEqual(response.status_code, 200)

    def test_get_dataset_list_details_error(self, mock_service, *_):
        mock_service.get_dataset_list_details.side_effect = ApplicationError(*errors.get(*self.test_error))

        response = self.app.get('/v1/dataset-list-details', headers=self.headers)

        expected_err = 'Failed to get detailed dataset list - {}'.format(errors.get_message(*self.test_error))
        self.assertEqual(response.get_json()['error'], expected_err)
        self.assertEqual(response.status_code, 500)

    def test_get_groups(self, mock_service, *_):
        case_id = 999
        mock_service.get_groups.return_value = (['test'], {})

        response = self.app.get('/v1/groups/{}'.format(case_id), headers=self.headers)

        mock_service.get_groups.assert_called_once_with(str(case_id))
        self.assertEqual(response.get_json(), ['test'])
        self.assertEqual(response.status_code, 200)

    def test_get_groups_error(self, mock_service, *_):
        case_id = 999
        mock_service.get_groups.side_effect = ApplicationError(*errors.get(*self.test_error))

        response = self.app.get('/v1/groups/{}'.format(case_id), headers=self.headers)

        expected_err = 'Failed to get groups - {}'.format(errors.get_message(*self.test_error))
        mock_service.get_groups.assert_called_once_with(str(case_id))
        self.assertEqual(response.get_json()['error'], expected_err)
        self.assertEqual(response.status_code, 500)

    def test_update_details_ok(self, mock_service, *_):
        expected_result = {'updated': True}
        mock_service.update_user_details.return_value = expected_result
        json_body = {'updated_data': {'contactable': True}, 'staff_id': 'aa111zz'}
        response = self.app.post('/v1/case/1/update', json=json_body, headers=self.headers)
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.get_json(), expected_result)

    def test_update_details_error(self, mock_service, *_):
        mock_service.update_user_details.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        json_body = {'updated_data': {'contactable': True}, 'staff_id': 'aa111zz'}
        response = self.app.post('/v1/case/1/update', json=json_body, headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        expected_err = 'Failed to update contact details - {}'.format(expected_err_msg)
        self.assertEqual(expected_err, response_body['error'])

    def test_get_users_dataset_activity_ok(self, mock_service, *_):
        mock_service.get_dataset_activity.return_value = {'test': 'data'}
        response = self.app.get('/v1/dataset-activity/1', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_get_users_dataset_activity_error(self, mock_service, *_):
        mock_service.get_dataset_activity.side_effect = ApplicationError(*errors.get(*self.test_error))
        expected_err_msg = errors.get_message(*self.test_error)

        response = self.app.get('/v1/dataset-activity/1', headers=self.headers)

        self.assertEqual(500, response.status_code)
        response_body = response.get_json()
        expected_err = 'Failed to get dataset activity - {}'.format(expected_err_msg)
        self.assertEqual(expected_err, response_body['error'])
