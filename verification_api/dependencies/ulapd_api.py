from flask import current_app, g
from verification_api.app import app
from verification_api.exceptions import ApplicationError
from common_utilities import errors
import requests


class UlapdAPI(object):
    """Encapsulating class for Ulapd API integration."""
    def __init__(self):
        self.url = current_app.config["ULAPD_API_URL"]
        self.timeout = current_app.config["DEFAULT_TIMEOUT"]

    def update(self, data):
        """Update user."""
        url = '{0}/users/contact_preference'.format(self.url)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = g.requests.patch(url, json=data, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from ulapd_api for user activation')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to ulapd_api for user activation')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout when writing to ulapd_api for user activation')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("Update user {}".format(data['user_id']))
            return {'message': 'user updated'}

    def get_dataset_list_details(self):
        """Get a detailed list of datasets in the service"""
        url = '{}/datasets?simple=true'.format(self.url)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = g.requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from ulapd_api when retrieving list of datasets')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to ulapd_api when retrieving list of datasets')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout with ulapd_api when retrieving list of datasets')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("Retrieved detailed list of datasets in the service")
            return response.json()

    # Data used to populate dataset activity
    def get_dataset_activity(self, user_id):
        """Get a users licence agreements and download history"""
        url = '{0}/users/dataset-activity/{1}'.format(self.url, user_id)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = g.requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from ulapd_api getting users dataset activity')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to ulapd_api getting users dataset activity')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout with ulapd_api getting users dataset activity')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("Retrieved details of the users dataset activity")
            return response.json()

    # Data used to populate data access checkboxes
    def get_user_dataset_access(self, user_id):
        """Get all datasets, their associated licences and whether the user has agreed those licences"""
        url = '{0}/users/dataset-access/{1}'.format(self.url, user_id)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = g.requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from ulapd_api getting users dataset access')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to ulapd_api getting users dataset access')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout with ulapd_api getting users dataset access')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("Retrieved details of the user's dataset access")
            return response.json()

    def update_dataset_access(self, data):
        """Update dataset access for user (add/remove licences to ulapd database LDAP roles)"""
        url = '{0}/users/licence'.format(self.url)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = g.requests.post(url, json=data, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from ulapd_api while updating dataset access')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to ulapd_api while updating dataset access')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout with ulapd_api getting while updating dataset access')
            raise ApplicationError(*errors.get("verification_api", "ULAPD_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("Updated user dataset access")
            return response.json()
