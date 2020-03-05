import os

# RULES OF CONFIG:
# 1. No region specific code. Regions are defined by setting the OS environment variables appropriately to build up the
# desired behaviour.
# 2. No use of defaults when getting OS environment variables. They must all be set to the required values prior to the
# app starting.
# 3. This is the only file in the app where os.environ should be used.

# For the enhanced logging extension
FLASK_LOG_LEVEL = os.environ['LOG_LEVEL']

# For health route
COMMIT = os.environ['COMMIT']

# This APP_NAME variable is to allow changing the app name when the app is running in a cluster. So that
# each app in the cluster will have a unique name.
APP_NAME = os.environ['APP_NAME']
MAX_HEALTH_CASCADE = int(os.environ['MAX_HEALTH_CASCADE'])
DEFAULT_TIMEOUT = int(os.environ['DEFAULT_TIMEOUT'])

# Following is an example of building the dependency structure used by the cascade route
# SELF can be used to demonstrate how it works (i.e. it will call it's own casecade
# route until MAX_HEALTH_CASCADE is hit)
# SELF = "http://localhost:8080"
# DEPENDENCIES = {"SELF": SELF}

SQL_HOST = os.environ['SQL_HOST']
SQL_DATABASE = os.environ['SQL_DATABASE']
SQL_PASSWORD = os.environ['SQL_PASSWORD']
APP_SQL_USERNAME = os.environ['APP_SQL_USERNAME']
ALEMBIC_SQL_USERNAME = os.environ['ALEMBIC_SQL_USERNAME']

if os.environ['SQL_USE_ALEMBIC_USER'] == 'yes':
    FINAL_SQL_USERNAME = ALEMBIC_SQL_USERNAME
else:
    FINAL_SQL_USERNAME = APP_SQL_USERNAME

SQLALCHEMY_DATABASE_URI = 'postgres://{0}:{1}@{2}/{3}'.format(FINAL_SQL_USERNAME, SQL_PASSWORD, SQL_HOST, SQL_DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False  # Explicitly set this in order to remove warning on run
SQLALCHEMY_POOL_RECYCLE = int(os.environ['SQLALCHEMY_POOL_RECYCLE'])

# Account
ACCOUNT_API_URL = os.environ['ACCOUNT_API_URL']
ACCOUNT_API_VERSION = os.environ['ACCOUNT_API_VERSION']
MASTER_API_KEY = os.environ['MASTER_API_KEY']

# Audit
AUDIT_API_URL = os.environ['AUDIT_API_URL']
AUDIT_API_VERSION = os.environ['AUDIT_API_VERSION']

# Ulapd-api
ULAPD_API_URL = os.environ['ULAPD_API_URL']

# Akuma
AKUMA_API_URL = os.environ['AKUMA_API_URL']
AKUMA_RETRY = os.environ['AKUMA_RETRY']

# Metric
METRIC_API_URL = os.environ['METRIC_API_URL']
METRIC_RETRY = os.environ['METRIC_RETRY']

DEPENDENCIES = {
    "Postgres": SQLALCHEMY_DATABASE_URI,
    "account-api": ACCOUNT_API_URL,
    "dps-metric-api": METRIC_API_URL
}
