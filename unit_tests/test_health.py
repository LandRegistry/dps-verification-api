import unittest
from unittest.mock import patch, MagicMock

from verification_api.main import app


class TestHealth(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_health(self):
        get_response = self.app.get('/health')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json['app'], u"verification-api")

    @patch('verification_api.views.general.current_app')
    @patch('verification_api.views.general.g')
    def test_health_cascade(self, mock_g, mock_app):
        mock_app.config.get.side_effect = _get_from_config
        mock_dependency_health = MagicMock()
        mock_dependency_health.status_code = 200
        mock_dependency_health.headers = {'content-type': 'application/json'}
        mock_dependency_health.json.return_value = {'data': 'TEST'}
        mock_g.requests.get.return_value = mock_dependency_health

        response = self.app.get('/health/cascade/1')
        response_json = response.get_json()
        response_service = response_json['services'][0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json['status'], 'OK')
        self.assertEqual(response_service['name'], 'dependency-api')
        self.assertEqual(response_service['status'], 'OK')
        self.assertEqual(response_service['content'], {'data': 'TEST'})

    @patch('verification_api.views.general.current_app')
    @patch('verification_api.views.general.g')
    def test_health_cascade_bad_dependency(self, mock_g, mock_app):
        mock_app.config.get.side_effect = _get_from_config
        mock_dependency_health = MagicMock()
        mock_dependency_health.status_code = 500
        mock_dependency_health.headers = {'content-type': 'application/json'}
        mock_dependency_health.json.return_value = {'data': 'TEST'}
        mock_g.requests.get.return_value = mock_dependency_health

        response = self.app.get('/health/cascade/1')
        response_json = response.get_json()
        response_service = response_json['services'][0]

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_json['status'], 'BAD')
        self.assertEqual(response_service['name'], 'dependency-api')
        self.assertEqual(response_service['status'], 'BAD')
        self.assertEqual(response_service['content'], {'data': 'TEST'})

    @patch('verification_api.views.general.current_app')
    @patch('verification_api.views.general.g')
    def test_health_cascade_unknown_dependency(self, mock_g, mock_app):
        mock_app.config.get.side_effect = _get_from_config
        mock_dependency_health = MagicMock()
        mock_dependency_health.status_code = 401
        mock_dependency_health.headers = {'content-type': 'application/json'}
        mock_dependency_health.json.return_value = {'data': 'TEST'}
        mock_g.requests.get.return_value = mock_dependency_health

        response = self.app.get('/health/cascade/1')
        response_json = response.get_json()
        response_service = response_json['services'][0]

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_json['status'], 'BAD')
        self.assertEqual(response_service['name'], 'dependency-api')
        self.assertEqual(response_service['status'], 'UNKNOWN')
        self.assertEqual(response_service['content'], {'data': 'TEST'})

    @patch('verification_api.views.general.current_app')
    @patch('verification_api.views.general.g')
    def test_health_cascade_connection_aborted(self, mock_g, mock_app):
        mock_app.config.get.side_effect = _get_from_config
        mock_g.requests.get.side_effect = ConnectionAbortedError('Test exception')

        response = self.app.get('/health/cascade/1')
        response_json = response.get_json()
        response_service = response_json['services'][0]

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_json['status'], 'BAD')
        self.assertEqual(response_service['name'], 'dependency-api')
        self.assertEqual(response_service['status'], 'UNKNOWN')
        self.assertIsNone(response_service['content'])

    @patch('verification_api.views.general.current_app')
    @patch('verification_api.views.general.g')
    def test_health_cascade_err(self, mock_g, mock_app):
        mock_app.config.get.side_effect = _get_from_config
        mock_g.requests.get.side_effect = Exception('Test exception')

        response = self.app.get('/health/cascade/1')
        response_json = response.get_json()
        response_service = response_json['services'][0]

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_json['status'], 'BAD')
        self.assertEqual(response_service['name'], 'dependency-api')
        self.assertEqual(response_service['status'], 'UNKNOWN')
        self.assertIsNone(response_service['content'])

    @patch('verification_api.views.general.current_app')
    def test_health_cascade_invalid_depth(self, mock_app):
        mock_app.config.get.side_effect = _get_from_config

        response = self.app.get('/health/cascade/10')
        response_json = response.get_json()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_json['status'], 'ERROR')
        self.assertEqual(response_json['cascade_depth'], 10)


def _get_from_config(*args, **_):
    if args[0] == 'MAX_HEALTH_CASCADE':
        return 1
    elif args[0] == 'APP_NAME':
        return 'Verification API'
    elif args[0] == 'DEPENDENCIES':
        return {
            'dependency-api': 'TEST_URL'
        }
    else:
        return 'variable not found'
