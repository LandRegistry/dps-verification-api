import unittest
import requests
from flask import current_app
from verification_api.main import app
from verification_api.exceptions import ApplicationError
from unittest.mock import patch
from verification_api.dependencies.account_api import AccountAPI
from requests.exceptions import HTTPError, ConnectionError, Timeout


class TestDependencyAccountAPI(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            self.app = app.test_client()
            self.url = current_app.config["ACCOUNT_API_URL"]
            self.version = current_app.config["ACCOUNT_API_VERSION"]
            self.timeout = current_app.config["DEFAULT_TIMEOUT"]
            self.error_msg = 'Test error message'
            self.key = current_app.config['MASTER_API_KEY']

    # ****** get ****** #
    @patch("requests.Session.get")
    def test_get(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.return_value.json.return_value = 'Success'
                mock_get.return_value.status_code = 200
                response = AccountAPI.get(self, '1234-567-890')
                self.assertEqual(response, 'Success')

    @patch("requests.Session.get")
    def test_get_with_timeout(self, mock_get):
        mock_get.side_effect = Timeout(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.get(self, '1234-567-890')
                    self.assertTrue(ApplicationError in str(context.exception))
                self.assertEqual(context.exception.message,
                                 'Connection to account_api timed out: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E503')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.get")
    def test_get_http_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.get(self, '1234-567-890')

                self.assertEqual(context.exception.message,
                                 'Received the following response from account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E501')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.get")
    def test_get_connection_error(self, mock_get):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_get.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.get(self, '1234-567-890')

                self.assertEqual(context.exception.message,
                                 'Encountered an error connecting to account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E502')
                self.assertEqual(context.exception.http_code, 500)

    # ****** approve ****** #
    @patch("requests.Session.post")
    def test_approve(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.return_value.text = 'Success'
                mock_post.return_value.status_code = 200
                response = AccountAPI.approve(self, '1234-567-890')
                assert response == {'message': 'approved'}

    @patch("requests.Session.post")
    def test_approve_with_timeout(self, mock_post):
        mock_post.side_effect = Timeout(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.approve(self, '1234-567-890')
                    self.assertTrue(ApplicationError in str(context.exception))
                self.assertEqual(context.exception.message,
                                 'Connection to account_api timed out: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E503')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_approve_http_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.approve(self, '1234-567-890')

                self.assertEqual(context.exception.message,
                                 'Received the following response from account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E501')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_approve_connection_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.approve(self, '1234-567-890')

                self.assertEqual(context.exception.message,
                                 'Encountered an error connecting to account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E502')
                self.assertEqual(context.exception.http_code, 500)

    # ****** decline ****** #
    @patch("requests.Session.post")
    def test_decline(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.return_value.text = 'Success'
                mock_post.return_value.status_code = 200
                response = AccountAPI.decline(self, '1234-567-890', 'Failed company checks', 'Reapply', '1')
                assert response == {'message': 'declined'}

    @patch("requests.Session.post")
    def test_decline_with_timeout(self, mock_post):
        mock_post.side_effect = Timeout(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.decline(self, '1234-567-890', 'Failed company checks', 'Reapply', '1')
                    self.assertTrue(ApplicationError in str(context.exception))
                self.assertEqual(context.exception.message,
                                 'Connection to account_api timed out: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E503')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_decline_http_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.decline(self, '1234-567-890', 'Failed company checks', 'Reapply', '1')

                self.assertEqual(context.exception.message,
                                 'Received the following response from account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E501')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_decline_connection_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.decline(self, '1234-567-890', 'Failed company checks', 'Reapply', '1')

                self.assertEqual(context.exception.message,
                                 'Encountered an error connecting to account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E502')
                self.assertEqual(context.exception.http_code, 500)

    # ****** close ****** #
    @patch("requests.Session.post")
    def test_close(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.return_value.text = 'Success'
                mock_post.return_value.status_code = 200
                response = AccountAPI.close(self, '1234-567-890', '0987-654-321', 'customer')
                assert response == {'message': 'closed'}

    @patch("requests.Session.post")
    def test_close_with_timeout(self, mock_post):
        mock_post.side_effect = Timeout(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.close(self, '1234-567-890', '0987-654-321', 'customer')
                    self.assertTrue(ApplicationError in str(context.exception))
                self.assertEqual(context.exception.message,
                                 'Connection to account_api timed out: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E503')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_close_http_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.close(self, '1234-567-890', '0987-654-321', 'customer')

                self.assertEqual(context.exception.message,
                                 'Received the following response from account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E501')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_close_connection_error(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.close(self, '1234-567-890', '0987-654-321', 'customer')

                self.assertEqual(context.exception.message,
                                 'Encountered an error connecting to account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E502')
                self.assertEqual(context.exception.http_code, 500)

    # ****** update_groups ****** #
    @patch("requests.Session.patch")
    def test_update_groups(self, mock_patch):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_patch.return_value.text = 'Success'
                mock_patch.return_value.status_code = 200
                response = AccountAPI.update_groups(self, '1234-567-890', {"nps": True})
                self.assertEqual(response, {'message': 'groups updated'})

    @patch("requests.Session.patch")
    def test_update_groups_with_timeout(self, mock_patch):
        mock_patch.side_effect = Timeout(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.update_groups(self, '1234-567-890', {"nps": True})
                    self.assertTrue(ApplicationError in str(context.exception))
                self.assertEqual(context.exception.message,
                                 'Connection to account_api timed out: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E503')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.patch")
    def test_update_groups_http_error(self, mock_patch):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_patch.side_effect = HTTPError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.update_groups(self, '1234-567-890', {"nps": True})

                self.assertEqual(context.exception.message,
                                 'Received the following response from account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E501')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.patch")
    def test_update_groups_connection_error(self, mock_patch):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_patch.side_effect = ConnectionError(self.error_msg)

                with self.assertRaises(ApplicationError) as context:
                    AccountAPI.update_groups(self, '1234-567-890', {"nps": True})

                self.assertEqual(context.exception.message,
                                 'Encountered an error connecting to account_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E502')
                self.assertEqual(context.exception.http_code, 500)
