from flask import current_app, g
from verification_api.app import app
from verification_api.exceptions import ApplicationError
from common_utilities import errors
import requests
import json


class AccountAPI(object):
    """Encapsulating class for Account API integration."""
    def __init__(self):
        self.url = current_app.config["ACCOUNT_API_URL"]
        self.version = current_app.config["ACCOUNT_API_VERSION"]
        self.timeout = current_app.config["DEFAULT_TIMEOUT"]
        self.key = current_app.config['MASTER_API_KEY']

    def get(self, ldap_id):
        url = '{0}/{1}/users?id={2}'.format(self.url, self.version, ldap_id)
        headers = {
            "Accept": "application/json",
            'Authorization': 'Bearer ' + self.key
        }
        try:
            response = g.requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from account_api for retrieving user details')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to account_api for retrieving user details')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout when writing to account_api for retrieving user details')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_TIMEOUT", filler=str(error)))
        else:
            return response.json()

    def approve(self, ldap_id):
        """Activate user."""
        url = '{0}/{1}/users/{2}/activate'.format(self.url, self.version, ldap_id)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            'Authorization': 'Bearer ' + self.key
        }

        try:
            response = g.requests.post(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from account_api for user activation')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to account_api for user activation')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout when writing to account_api for user activation')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("Activated user {}".format(ldap_id))
            return {'message': 'approved'}

    def decline(self, ldap_id, decline_reason, decline_advice, user_id):
        """Decline user."""
        url = '{0}/{1}/users/decline'.format(self.url, self.version)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            'Authorization': 'Bearer ' + self.key
        }
        reason = {
            'ldap_id': ldap_id,
            'reason': decline_reason,
            'advice': decline_advice,
            'user_id': user_id
        }
        try:
            response = g.requests.post(url, data=json.dumps(reason), headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from account_api for declining user')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to account_api for declining user')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout when writing to account_api for declining user')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("Declined user {}".format(ldap_id))
            return {'message': 'declined'}

    def close(self, ldap_id, user_id, requester):
        """Close users account"""
        url = '{0}/{1}/users/close'.format(self.url, self.version)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            'Authorization': 'Bearer ' + self.key
        }
        closure_data = {
            'ldap_id': ldap_id,
            'user_id': user_id,
            'requester': requester
        }
        try:
            response = g.requests.post(url, data=json.dumps(closure_data), headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from account_api for closing account')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to account_api for closing account')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout when writing to account_api for closing account')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("closed account for user {}".format(ldap_id))
            return {'message': 'closed'}

    def update_groups(self, ldap_id, groups):
        """Close users account"""
        url = '{0}/{1}/users/update_groups'.format(self.url, self.version)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            'Authorization': 'Bearer ' + self.key
        }
        data = {
            'ldap_id': ldap_id,
            'groups': groups
        }
        try:
            response = g.requests.patch(url, data=json.dumps(data), headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            current_app.logger.error('Encountered non 2xx http code from account_api for updating groups')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_HTTP_ERROR", filler=str(error)))
        except requests.exceptions.ConnectionError as error:
            current_app.logger.error('Encountered an error connecting to account_api for updating group')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_CONN_ERROR", filler=str(error)))
        except requests.exceptions.Timeout as error:
            current_app.logger.error('Encountered a timeout when writing to account_api for updating group')
            raise ApplicationError(*errors.get("verification_api", "ACCOUNT_API_TIMEOUT", filler=str(error)))
        else:
            app.logger.info("groups updated for user {}".format(ldap_id))
            return {'message': 'groups updated'}
