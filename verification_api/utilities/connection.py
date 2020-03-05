from verification_api.app import app
import psycopg2


def connect(cursor_factory=None):
    connection = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
    return connection.cursor(cursor_factory=cursor_factory)


def complete(cursor):
    cursor.connection.commit()
    cursor.close()
    cursor.connection.close()


def rollback(cursor):
    cursor.connection.rollback()
    cursor.close()
    cursor.connection.close()
