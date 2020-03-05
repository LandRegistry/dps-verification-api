from flask import current_app, g
from verification_api.app import app
from verification_api.exceptions import ApplicationError
from common_utilities import errors
import requests


class MetricAPI(object):
    """Encapsulating class for Metric API integration."""

    def __init__(self):
        self.url = current_app.config["METRIC_API_URL"]
        self.timeout = current_app.config["DEFAULT_TIMEOUT"]

    def add_event(self, payload):
        url = '{}/v1/metric'.format(self.url)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = g.requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from dps_metric_api for adding event')
            raise ApplicationError(*errors.get("verification_api", "METRIC_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to dps_metric_api for adding event')
            raise ApplicationError(*errors.get("verification_api", "METRIC_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout when writing to dps_metric_api for adding event')
            raise ApplicationError(*errors.get("verification_api", "METRIC_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("added event")
            return {'message': 'event added'}


def insert_metric_event(activity, data):
    try:
        data.update(data['registration_data'])
        data.pop('registration_data')
        data['activity_type'] = activity

        payload = _create_metric_payload(data)
        event = MetricAPI()

        metric_retries = int(current_app.config["METRIC_RETRY"])
        for attempts in range(metric_retries):
            try:
                app.logger.info('Attempt {} to call Metric API'.format(attempts))
                event.add_event(payload)
                app.logger.info('Call to Metric API successful')
                break
            except Exception as e:
                app.logger.error('Call to Metric API failed on attempt {} with error: {}'.format(attempts, e))
    except ApplicationError as error:
        app.logger.error('Verification-api failed calling Metric API with error: {}'.format(str(error)))
        app.logger.info(activity, data)


def handle_dataset_access_metrics(case_details, updated_access):
    for licence in updated_access['licences']:
        data = {}
        data.update(case_details)
        data['dataset'] = licence['licence_id']
        activity = 'role added' if licence['agreed'] else 'role removed'
        insert_metric_event(activity, data)


def _create_metric_payload(data):
    payload = {
        'user': {},
        'activity': {
            'dataset': None,
            'filename': None
        }
    }

    for key, value in data.items():
        if key in 'user_id':
            payload['user']['ckan_user_id'] = value

        if key in ['user_type', 'status']:
            payload['user'][key] = value

        if key in ['activity_type', 'dataset']:
            payload['activity'][key] = value

    return payload
