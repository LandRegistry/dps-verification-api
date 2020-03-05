# Set the base image to the base image
FROM hmlandregistry/dev_base_python_flask:5-3.6

ENV SQL_HOST=postgres \
 SQL_DATABASE=dps \
 ALEMBIC_SQL_USERNAME=root \
 SQL_USE_ALEMBIC_USER=no \
 APP_SQL_USERNAME=dps \
 SQL_PASSWORD=dps \
 SQLALCHEMY_POOL_RECYCLE="3300"

# ----
# Put your app-specific stuff here (extra yum installs etc).
# Any unique environment variables your config.py needs should also be added as ENV entries here

ENV APP_NAME="verification-api" \
 MAX_HEALTH_CASCADE="6" \
 LOG_LEVEL="DEBUG" \
 DEFAULT_TIMEOUT="30" \
 ACCOUNT_API_URL="http://account-api:8080" \
 ACCOUNT_API_VERSION="v1" \
 ULAPD_API_URL="http://ulapd-api:8080/v1" \
 MASTER_API_KEY="PLACEHOLDER" \
 METRIC_API_URL="http://dps-metric-api:8080" \
 METRIC_RETRY="3"

# ----

# The command to run the app is inherited from lr_base_python_flask

# Get the python environment ready.
# Have this at the end so if the files change, all the other steps don't need to be rerun. Same reason why _test is
# first. This ensures the container always has just what is in the requirements files as it will rerun this in a
# clean image.
ADD requirements_test.txt requirements_test.txt
ADD requirements.txt requirements.txt
RUN pip3 install -q -r requirements.txt && \
  pip3 install -q -r requirements_test.txt
