import unittest
import requests
from common_utilities import errors
from flask import current_app
from verification_api.main import app
from verification_api.exceptions import ApplicationError
from unittest.mock import patch
from verification_api.dependencies.ulapd_api import UlapdAPI
from requests.exceptions import HTTPError, ConnectionError, Timeout


class TestDependencyUlapdAPI(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            self.app = app.test_client()
            self.url = current_app.config["ULAPD_API_URL"]
            self.timeout = current_app.config["DEFAULT_TIMEOUT"]
            self.error_msg = 'Test error message'
            self.updated_data = {'user_id': '123', 'contactable': True}
            self.headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

    @patch("requests.Session.patch")
    def test_update(self, mock_patch):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_patch.return_value.text = 'Success'
                mock_patch.return_value.status_code = 200
                response = UlapdAPI.update(self, self.updated_data)
                assert response == {'message': 'user updated'}

    @patch("requests.Session.patch")
    def test_update_with_timeout(self, mock_patch):
        mock_patch.side_effect = Timeout(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.update(self, self.updated_data)
                    self.assertTrue(ApplicationError in str(context.exception))
                self.assertEqual(context.exception.message,
                                 'Connection to ulapd_api timed out: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E519')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.patch")
    def test_update_http_error(self, mock_patch):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_patch.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.update(self, self.updated_data)

                self.assertEqual(context.exception.message,
                                 'Received the following response from ulapd_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E517')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.patch")
    def test_update_connection_error(self, mock_patch):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_patch.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.update(self, self.updated_data)

                self.assertEqual(context.exception.message,
                                 'Encountered an error connecting to ulapd_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E518')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.get")
    def test_get_dataset_list_details(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                dataset_list = [{'title': 'Test Dataset',
                                 'id': '1',
                                 'private': False, 'name': 'test'}]
                mock_get.return_value.json.return_value = dataset_list
                mock_get.return_value.status_code = 200

                response = UlapdAPI.get_dataset_list_details(self)

                mock_get.assert_called_once()
                self.assertEqual(response, dataset_list)

    @patch("requests.Session.get")
    def test_get_dataset_list_details_with_timeout(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = Timeout(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_dataset_list_details(self)

                expected_err = ('verification_api', 'ULAPD_API_TIMEOUT')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_dataset_list_details_http_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_dataset_list_details(self)

                expected_err = ('verification_api', 'ULAPD_API_HTTP_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_dataset_list_details_connection_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_dataset_list_details(self)

                expected_err = ('verification_api', 'ULAPD_API_CONN_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_dataset_activity(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                dataset_activity = [
                    {
                        "download_history": [],
                        "id": 356,
                        "licence_agreed": False,
                        "name": "ccod",
                        "private": False,
                        "title": "UK companies that own property in England and Wales"
                    }
                ]

                mock_get.return_value.json.return_value = dataset_activity
                mock_get.return_value.status_code = 200

                response = UlapdAPI.get_dataset_activity(self, 1)

                mock_get.assert_called_once()
                mock_get.assert_called_with(
                    '{0}/users/dataset-activity/{1}'.format(self.url, 1),
                    headers=self.headers,
                    timeout=self.timeout
                )

                self.assertEqual(response, dataset_activity)

    @patch("requests.Session.get")
    def test_get_dataset_activity_timeout(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = Timeout(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_dataset_activity(self, 1)

                expected_err = ('verification_api', 'ULAPD_API_TIMEOUT')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_dataset_activity_http_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_dataset_activity(self, 1)

                expected_err = ('verification_api', 'ULAPD_API_HTTP_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_dataset_activity_connection_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_dataset_activity(self, 1)

                expected_err = ('verification_api', 'ULAPD_API_CONN_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_user_dataset_access(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                dataset_access = [
                    {
                        'name': 'res_cov',
                        'title': 'Restrictive Covenants',
                        'licences': {
                            'res_cov_direct': {
                                'title': 'Direct Use',
                                'agreed': True
                            }
                        }
                    }
                ]

                mock_get.return_value.json.return_value = dataset_access
                mock_get.return_value.status_code = 200

                response = UlapdAPI.get_user_dataset_access(self, 1)

                mock_get.assert_called_once()
                mock_get.assert_called_with(
                    '{0}/users/dataset-access/{1}'.format(self.url, 1),
                    headers=self.headers,
                    timeout=self.timeout
                )

                self.assertEqual(response, dataset_access)

    @patch("requests.Session.get")
    def test_get_user_dataset_access_timeout(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = Timeout(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_user_dataset_access(self, 1)

                expected_err = ('verification_api', 'ULAPD_API_TIMEOUT')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_user_dataset_access_http_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_user_dataset_access(self, 1)

                expected_err = ('verification_api', 'ULAPD_API_HTTP_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.get")
    def test_get_user_dataset_access_connection_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.get_user_dataset_access(self, 1)

                expected_err = ('verification_api', 'ULAPD_API_CONN_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_get.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.post")
    def test_update_dataset_access(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                input_data = {
                    'user_details_id': 1,
                    'licences': [
                        {'licence_id': 'nps', 'agreed': True}
                    ]
                }

                mock_post.return_value.json.return_value = {'nps': True}
                mock_post.return_value.status_code = 200

                response = UlapdAPI.update_dataset_access(self, input_data)

                mock_post.assert_called_once()
                mock_post.assert_called_with(
                    '{0}/users/licence'.format(self.url),
                    json=input_data,
                    headers=self.headers,
                    timeout=self.timeout
                )

                self.assertEqual(response, {'nps': True})

    @patch("requests.Session.post")
    def test_update_dataset_access_timeout(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = Timeout(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.update_dataset_access(self, {})

                expected_err = ('verification_api', 'ULAPD_API_TIMEOUT')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_post.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.post")
    def test_update_dataset_access_http_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.update_dataset_access(self, {})

                expected_err = ('verification_api', 'ULAPD_API_HTTP_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_post.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)

    @patch("requests.Session.post")
    def test_update_dataset_access_connection_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    UlapdAPI.update_dataset_access(self, {})

                expected_err = ('verification_api', 'ULAPD_API_CONN_ERROR')
                expected_err_message = errors.get_message(*expected_err, filler=self.error_msg)
                expected_err_code = errors.get_code(*expected_err)

                mock_post.assert_called_once()
                self.assertEqual(context.exception.message, expected_err_message)
                self.assertEqual(context.exception.code, expected_err_code)
