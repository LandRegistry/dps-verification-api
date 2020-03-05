import json
import uuid
import os

from verification_api.main import app
from verification_api.models import Case
from verification_api.extensions import db


def insert_dst_case(case_data):
    with app.app_context():
        case = Case(case_data)
        db.session.add(case)
        db.session.commit()
        case_id = case.verification_id
        db.session.close()
    return case_id


def teardown_dst_case(case_id):
    if case_id is None:
        return
    with app.app_context():
        case = Case.query.filter_by(verification_id=case_id).first()
        db.session.delete(case)
        db.session.commit()
        db.session.close()


def get_dst_case(case_id):
    with app.app_context():
        case = Case.get_case_by_id(case_id)
    return case


def get_dst_case_by_ldap_id(ldap_id):
    with app.app_context():
        case = Case.get_case_by_ldap_id(ldap_id)
    return case


def get_dst_pending_cases():
    with app.app_context():
        cases = Case.get_pending()
    return cases


def make_uuid():
    return uuid.uuid4()


def get_json_from_file(directory, file_path):
    full_path = os.path.join(directory, file_path)
    with open(full_path, 'r') as file:
        raw_data = file.read()

    return json.loads(raw_data)
