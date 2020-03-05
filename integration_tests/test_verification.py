import unittest
import json
import requests
import traceback
from os import path
from flask import current_app, g
from verification_api.main import app
from verification_api.extensions import db
from integration_tests.utilities import helpers


class TestVerificationAPI(unittest.TestCase):

    URL_VERIFICATION_PREFIX = '/v1'
    directory = path.dirname(__file__)
    case_data = helpers.get_json_from_file(directory, 'data/user_registration.json')
    ldap_data = helpers.get_json_from_file(directory, 'data/ldap_user.json')
    ulapd_user = helpers.get_json_from_file(directory, 'data/ulapd_user.json')
    ulapd_user['name'] = str(helpers.make_uuid())
    staff_id = 'LRTM101'

    with app.app_context():
        ulapd_url = current_app.config['ULAPD_API_URL']
        account_url = '{}/{}'.format(current_app.config['ACCOUNT_API_URL'], current_app.config['ACCOUNT_API_VERSION'])

    def setUp(self):
        self.client = app.test_client()

        with app.app_context():
            self.headers = {'Accept': 'application/json',
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + current_app.config['MASTER_API_KEY']}

        self.ldap_id, self.ulapd_id, self.case_id = (None,) * 3
        self.skip_test = False
        try:
            app.logger.info('Setting up service user...')
            self._setup_service_user()
            app.logger.info('Done.')

            app.logger.info('Setting up DST case...')
            self.case_id = helpers.insert_dst_case(self.case_data)
            app.logger.info('Done.'.format(self.case_id))
        except Exception:
            self.skip_test = True
            app.logger.error('Setup failed, skipping test')
            traceback.print_exc()
            self.tearDown()

    def tearDown(self):
        self._teardown_service_user()
        helpers.teardown_dst_case(self.case_id)

        if self.skip_test:
            self.assertTrue(False, 'Setup failed')

    def test_insert_case(self):
        url = '{}/case'.format(self.URL_VERIFICATION_PREFIX)
        response = self.client.post(url, data=json.dumps(self.case_data),
                                    headers=self.headers)
        self.assertEqual(201, response.status_code)
        response_body = response.get_json()
        self.assertIn('case_id', response_body)

        case = helpers.get_dst_case(response_body['case_id'])
        self.assertIsNotNone(case)
        self.assertEqual(case.status, 'Pending')

    def test_worklist(self):
        url = '{}/worklist'.format(self.URL_VERIFICATION_PREFIX)
        response = self.client.get(url, headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = json.loads(response.data.decode())

        expected_cases = helpers.get_dst_pending_cases()
        expected_num = len(expected_cases)
        self.assertEqual(len(response_body), expected_num)

    def test_case_by_id(self):
        url = '{}/case/{}'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.get(url, headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()

        self.assertEqual(response_body['case_id'], self.case_id)
        self.assertEqual(response_body['status'], 'Pending')
        self.assertIn('registration_data', response_body)
        self.assertIn('staff_id', response_body)
        self.assertIn('notes', response_body)

    def test_add_note(self):
        notepad = {
            'staff_id': self.staff_id,
            'note_text': 'A notepad entry'
        }
        url = '{}/case/{}/note'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.post(url, data=json.dumps(notepad), headers=self.headers)

        self.assertEqual(201, response.status_code)

        # Retrieve notes
        url = '{}/case/{}'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(200, response.status_code)
        response_body = response.get_json()

        self.assertEqual(response_body['notes'][0]['note_text'], notepad['note_text'])

    def test_add_note_locked(self):
        notepad = {
            'staff_id': 'SOMEONE_ELSE',
            'note_text': 'A notepad entry'
        }
        url = '{}/case/{}/note'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.post(url, data=json.dumps(notepad), headers=self.headers)

        self.assertEqual(response.status_code, 403)
        response_body = response.get_json()
        expected_error = 'Locking error: Could not add note to case as it is locked to another user'
        self.assertEqual(response_body['error'], 'Failed to insert note - {}'.format(expected_error))

        # Retrieve notes
        url = '{}/case/{}'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(200, response.status_code)
        response_body = response.get_json()

        self.assertEqual(len(response_body['notes']), 0)

    def test_approve(self):
        case = helpers.get_dst_case_by_ldap_id(self.ldap_id)
        case_id = case.verification_id
        approve_body = {
            'staff_id': self.staff_id
        }
        url = '{}/case/{}/approve'.format(self.URL_VERIFICATION_PREFIX, case_id)
        response = self.client.post(url, data=json.dumps(approve_body), headers=self.headers)

        self.assertEqual(response.status_code, 200)
        response_body = response.get_json()
        assert response_body['status_updated'] is True

        case = helpers.get_dst_case(case_id)
        self.assertEqual(case.status, 'Approved')

    def test_approve_locked(self):
        approve_body = {
            'staff_id': 'SOMEONE_ELSE'
        }
        url = '{}/case/{}/approve'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.post(url, data=json.dumps(approve_body), headers=self.headers)

        self.assertEqual(response.status_code, 403)
        response_body = response.get_json()
        expected_error = 'Locking error: Could not perform action on case as it is locked to another user'
        self.assertEqual(response_body['error'], 'Failed to approve case - {}'.format(expected_error))

        case = helpers.get_dst_case(self.case_id)
        self.assertEqual(case.status, 'Pending')

    def test_decline(self):
        case = helpers.get_dst_case_by_ldap_id(self.ldap_id)
        case_id = case.verification_id
        decline = {
            'staff_id': self.staff_id,
            'reason': 'Company number incorrect',
            'advice': 'Reapply with correct info'
        }
        url = '{}/case/{}/decline'.format(self.URL_VERIFICATION_PREFIX, case_id)
        response = self.client.post(url, data=json.dumps(decline), headers=self.headers)
        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        assert response_body['status_updated'] is True

        case = helpers.get_dst_case(case_id)
        self.assertEqual(case.status, 'Declined')

        self.ldap_id = None
        self.ulapd_id = None

    def test_decline_locked(self):
        decline = {
            'staff_id': 'SOMEONE_ELSE',
            'reason': 'Company number incorrect',
            'advice': 'Reapply with correct info'
        }
        url = '{}/case/{}/decline'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.post(url, data=json.dumps(decline), headers=self.headers)

        self.assertEqual(response.status_code, 403)
        response_body = response.get_json()
        expected_error = 'Locking error: Could not perform action on case as it is locked to another user'
        self.assertEqual(response_body['error'], 'Failed to decline case - {}'.format(expected_error))

        case = helpers.get_dst_case(self.case_id)
        self.assertEqual(case.status, 'Pending')

    def test_decline_reasons(self):
        url = '{}/decline-reasons'.format(self.URL_VERIFICATION_PREFIX)
        response = self.client.get(url, headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        assert len(response_body) > 0
        assert 'decline_reason' in response_body[0]

    def test_close(self):
        # Setup - can only close active accounts
        case = helpers.get_dst_case_by_ldap_id(self.ldap_id)
        case_id = case.verification_id
        approve_body = {
            'staff_id': self.staff_id
        }
        url = '{}/case/{}/approve'.format(self.URL_VERIFICATION_PREFIX, case_id)
        response = self.client.post(url, data=json.dumps(approve_body), headers=self.headers)
        self.assertEqual(response.status_code, 200, 'Setup failed - unable to approve DST case')

        close = {
            'staff_id': 'AA123ZZ',
            'close_detail': 'LR wants a closure',
            'requester': 'hmlr'
        }
        url = '{}/case/{}/close'.format(self.URL_VERIFICATION_PREFIX, case_id)
        response = self.client.post(url, data=json.dumps(close), headers=self.headers)

        self.assertEqual(200, response.status_code)
        close_body = response.get_json()
        self.assertTrue(close_body['status_updated'])

        with app.app_context():
            rows = db.session.execute("select v.status, c.close_detail from verification v, close c "
                                      "where v.verification_id = {} and "
                                      "v.verification_id = c.verification_id;".format(case_id))
            for row in rows:
                data = row
                self.assertEqual(data['status'], 'Closed')
                self.assertEqual(data['close_detail'], 'LR wants a closure')

    def test_update_details(self):
        url = '{}/case/{}/update'.format(self.URL_VERIFICATION_PREFIX, self.case_id)

        data = {
            'updated_data': {
                'contactable': False,
                'contact_preferences': []
            },
            'staff_id': self.staff_id
        }

        response = self.client.post(url, data=json.dumps(data), headers=self.headers)
        self.assertEqual(response.status_code, 200)

        body = response.get_json()
        self.assertTrue(body['updated'])

        case = helpers.get_dst_case(self.case_id)
        self.assertEqual(case.registration_data['contactable'], False)

    def test_lock(self):
        test_staff_id = 'LRTM999'
        lock_body = {
            'staff_id': test_staff_id
        }
        url = '{}/case/{}/lock'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.post(url, data=json.dumps(lock_body), headers=self.headers)

        self.assertEqual(response.status_code, 204)

        case = helpers.get_dst_case(self.case_id)
        self.assertEqual(case.staff_id, test_staff_id)

    def test_unlock(self):

        url = '{}/case/{}/unlock'.format(self.URL_VERIFICATION_PREFIX, self.case_id)
        response = self.client.post(url, data=json.dumps({}), headers=self.headers)

        self.assertEqual(response.status_code, 204)

        case = helpers.get_dst_case(self.case_id)
        self.assertIsNone(case.staff_id)

    def test_search(self):
        search_params = {
            "first_name": "rob",
            "last_name": "",
            "organisation_name": "",
            "email": "",
        }
        url = '{}/search'.format(self.URL_VERIFICATION_PREFIX)
        response = self.client.post(url, data=json.dumps(search_params), headers=self.headers)

        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertTrue(len(response_body) > 0)
        self.assertEqual(response_body[0]['status'], 'Pending')
        self.assertEqual(response_body[0]['registration_data']['first_name'], 'Rob')

    def test_search_no_result(self):
        search_params = {
            "first_name": "Extremeleyunlikelyfirstname",
            "last_name": "",
            "organisation_name": "",
            "email": "",
        }
        url = '{}/search'.format(self.URL_VERIFICATION_PREFIX)
        response = self.client.post(url, data=json.dumps(search_params), headers=self.headers)
        self.assertEqual(200, response.status_code)
        response_body = response.get_json()
        self.assertEqual(len(response_body), 0)

    # ----[ Helper Functions ]---- #

    def _setup_service_user(self):
        with app.app_context() as ac:
            ac.g.requests = requests.Session()
            with app.test_request_context():
                url = self.ulapd_url + '/users'
                data = json.dumps(self.ulapd_user)
                ulapd_response = g.requests.post(url, data=data, headers=self.headers)
                self.assertEqual(201, ulapd_response.status_code)
                ulapd_body = json.loads(ulapd_response.text)
                self.ldap_id = ulapd_body['ldap_id']
                self.ulapd_id = str(ulapd_body['user_details_id'])
                self.case_data['user_id'] = self.ulapd_id

    def _teardown_service_user(self):
        if self.ldap_id is None:
            return

        with app.app_context() as ac:
            ac.g.requests = requests.Session()
            with app.test_request_context():

                url = '{}/users/{}'.format(self.account_url, self.ldap_id)
                g.requests.delete(url, headers=self.headers)

                if self.ulapd_id is None:
                    return

                url = self.ulapd_url + '/users/' + self.ulapd_id
                g.requests.delete(url, headers=self.headers)
