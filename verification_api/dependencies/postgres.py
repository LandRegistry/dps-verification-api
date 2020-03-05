from flask import current_app
import psycopg2
from verification_api.exceptions import ApplicationError


def get_current_timestamp():
    try:
        conn = psycopg2.connect(current_app.config['SQLALCHEMY_DATABASE_URI'])
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_TIMESTAMP;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0]
    except psycopg2.DataError as e:
        raise ApplicationError(
            'Input data error: ' + str(e), 'DB', http_code=400)
    except (psycopg2.OperationalError, psycopg2.ProgrammingError) as e:
        raise ApplicationError(
            'Database error: ' + str(e), 'DB', http_code=400)
