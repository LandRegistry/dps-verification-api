import unittest
import requests
from flask import current_app
from verification_api.main import app
from verification_api.exceptions import ApplicationError
from unittest.mock import patch
from verification_api.dependencies.metric_api import (MetricAPI,
                                                      _create_metric_payload,
                                                      insert_metric_event,
                                                      handle_dataset_access_metrics)
from requests.exceptions import HTTPError, ConnectionError, Timeout
from common_utilities import errors


class TestDependencyMetricAPI(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            self.app = app.test_client()
            self.url = current_app.config["METRIC_API_URL"]
            self.timeout = current_app.config["DEFAULT_TIMEOUT"]
            self.error_msg = "Test error"
            self.payload = {
                'registration_data': {
                    'user_id': '123-456-abc',
                    'status': 'Pending',
                    'user_type': 'organisation-uk'
                }
            }

    @patch('verification_api.dependencies.metric_api.current_app')
    def test_new_metric_api(self, mock_app):
        test_url = 'http://metric-api-url:8080'
        test_timeout = '30'

        mock_app.config = {
            'METRIC_API_URL': test_url,
            'DEFAULT_TIMEOUT': test_timeout,
        }

        test_api = MetricAPI()
        self.assertEqual(test_api.url, test_url)
        self.assertEqual(test_api.timeout, test_timeout)

    @patch("requests.Session.post")
    def test_add_event_success(self, mock_post):
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                mock_post.return_value.text = 'Success'
                mock_post.return_value.status_code = 200
                response = MetricAPI.add_event(self, self.payload)
                self.assertEqual(response, {'message': 'event added'})

    @patch("requests.Session.post")
    def test_add_event_with_timeout(self, mock_post):
        mock_post.side_effect = Timeout(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    MetricAPI.add_event(self, self.payload)

                self.assertEqual(context.exception.message,
                                 'Connection to dps_metric_api timed out: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E516')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_add_event_http_error(self, mock_post):
        mock_post.side_effect = HTTPError(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    MetricAPI.add_event(self, self.payload)

                self.assertEqual(context.exception.message,
                                 'Received the following response from dps_metric_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E514')
                self.assertEqual(context.exception.http_code, 500)

    @patch("requests.Session.post")
    def test_add_event_connection_error(self, mock_post):
        mock_post.side_effect = ConnectionError(self.error_msg)
        with app.app_context() as ac:
            ac.g.trace_id = None
            ac.g.requests = requests.Session()
            with app.test_request_context():
                with self.assertRaises(ApplicationError) as context:
                    MetricAPI.add_event(self, self.payload)

                self.assertEqual(context.exception.message,
                                 'Encountered an error connecting to dps_metric_api: {}'.format(self.error_msg))
                self.assertEqual(context.exception.code, 'E515')
                self.assertEqual(context.exception.http_code, 500)

    @patch("verification_api.dependencies.metric_api.MetricAPI")
    @patch("verification_api.dependencies.metric_api._create_metric_payload")
    def test_insert_metric_event_success(self, mock_create_payload, mock_metric_api, *_):
        mock_metric_api.add_event.return_value = {'foo': 'bar'}
        with app.app_context() as ac:
            ac.g.trace_id = None
            insert_metric_event('dst_action_approved', self.payload)
        mock_create_payload.assert_called_once()

    @patch("verification_api.dependencies.metric_api.MetricAPI")
    @patch("verification_api.dependencies.metric_api._create_metric_payload")
    def test_insert_metric_event_error(self, mock_create_payload, mock_metric_api, *_):
        mock_create_payload.return_value = {'foo': 'bar'}
        error = ApplicationError(*errors.get("verification_api", "METRIC_API_HTTP_ERROR"))
        mock_metric_api.return_value.add_event.side_effect = error
        with app.app_context() as ac:
            metric_retry = current_app.config["METRIC_RETRY"]
            ac.g.trace_id = None
            insert_metric_event('dst_action_approved', self.payload)
        self.assertEqual(mock_metric_api.return_value.add_event.call_count, int(metric_retry))

    @patch("verification_api.dependencies.metric_api.app")
    @patch("verification_api.dependencies.metric_api._create_metric_payload")
    def test_insert_metric_event_app_error(self, mock_create_payload, mock_app, *_):
        error = ApplicationError(*errors.get("verification_api", "METRIC_API_HTTP_ERROR"))
        mock_create_payload.side_effect = error

        insert_metric_event('dst_action_approved', self.payload)

        error_msg = 'Verification-api failed calling Metric API with error: {}'.format(str(error))
        mock_app.logger.error.assert_called_with(error_msg)

    @patch("verification_api.dependencies.metric_api.insert_metric_event")
    def test_handle_dataset_access_metrics(self, mock_insert_metric):
        case_details = self.payload
        updated_access = {
            'user_details_id': 123,
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

        handle_dataset_access_metrics(case_details, updated_access)

        self.assertEqual(mock_insert_metric.call_count, 2)
        case_details['dataset'] = 'nps'
        mock_insert_metric.assert_any_call('role added', case_details)
        case_details['dataset'] = 'dad'
        mock_insert_metric.assert_any_call('role removed', case_details)

    def test_create_metric_payload(self):
        metric_data = self.payload['registration_data']
        metric_data['activity_type'] = 'dst_action_approved'

        expected = {
            'user': {
                'ckan_user_id': '123-456-abc',
                'status': 'Pending',
                'user_type': 'organisation-uk'
            },
            'activity': {
                'activity_type': 'dst_action_approved',
                'filename': None,
                'dataset': None
            }
        }

        result = _create_metric_payload(metric_data)
        self.assertDictEqual(result, expected)
