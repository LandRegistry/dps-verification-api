import datetime
from verification_api.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import asc, desc


class Case(db.Model):
    __tablename__ = 'verification'
    verification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    ldap_id = db.Column(db.String, nullable=False)
    registration_data = db.Column(JSONB, nullable=False)
    status = db.Column(db.String, nullable=False)
    date_added = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    staff_id = db.Column(db.String, nullable=True)
    date_agreed = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = relationship(
        'Note',
        cascade='all, delete, delete-orphan'
    )
    closure = relationship(
        'Close',
        cascade='all, delete, delete-orphan'
    )

    def __init__(self, user_data):
        self.user_id = user_data['user_id']
        self.ldap_id = user_data['ldap_id']
        self.registration_data = user_data['registration_data']
        self.status = user_data['status']
        self.staff_id = user_data.get('staff_id', None)
        self.date_agreed = None

    @staticmethod
    def get_case_by_id(case_id):
        return Case.query.filter_by(verification_id=case_id).first()

    @staticmethod
    def get_case_by_ldap_id(ldap_id):
        return Case.query.filter_by(ldap_id=ldap_id).first()

    @staticmethod
    def get_pending():
        return Case.query.filter_by(status='Pending').order_by(desc(Case.date_added)).all()

    @staticmethod
    def search(first_name=None, last_name=None, organisation_name=None, email=None):
        filters = []
        if first_name:
            filters.append(Case.registration_data['first_name'].astext.ilike('%' + first_name + '%'))
        if last_name:
            filters.append(Case.registration_data['last_name'].astext.ilike('%' + last_name + '%'))
        if organisation_name:
            org = '%' + organisation_name + '%'
            filters.append(Case.registration_data['organisation_name'].astext.ilike(org))
        if email:
            filters.append(Case.registration_data['email'].astext.ilike('%' + email + '%'))

        return Case.query.filter(*filters)

    def as_dict(self):
        status = self.status
        if status == 'Pending' and len(self.notes) > 0:
            status = 'In Progress'

        return {
            'case_id': self.verification_id,
            'user_id': self.user_id,
            'ldap_id': self.ldap_id,
            'registration_data': self.registration_data,
            'date_added': str(self.date_added),
            'staff_id': self.staff_id,
            'date_agreed': str(self.date_agreed),
            'status': status
        }


class Note(db.Model):
    __tablename__ = 'note'
    note_id = db.Column(db.Integer, primary_key=True)
    verification_id = db.Column(db.Integer, db.ForeignKey('verification.verification_id'), nullable=False)
    note_detail = db.Column(db.String, nullable=False)
    staff_id = db.Column(db.String, nullable=True)
    date_added = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __init__(self, notepad):
        self.verification_id = notepad['case_id']
        self.note_detail = notepad['note_text']
        self.staff_id = notepad['staff_id']

    @staticmethod
    def get_notepad_by_case_id(case_id):
        return Note.query.filter_by(verification_id=case_id).order_by(desc(Note.date_added)).all()

    def as_dict(self):
        return {
            'note_id': self.note_id,
            'case_id': self.verification_id,
            'note_text': self.note_detail,
            'staff_id': self.staff_id,
            'date_added': str(self.date_added)
        }


class DeclineReason(db.Model):
    __tablename__ = 'decline_reason'
    decline_id = db.Column(db.Integer, primary_key=True)
    decline_description = db.Column(db.String, nullable=False)
    decline_detail = db.Column(db.String, nullable=False)
    date_added = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    date_ended = db.Column(db.DateTime(timezone=True), nullable=True)
    decline_advice = db.Column(db.String, nullable=False)

    def __init__(self, decline):
        self.decline_description = decline['decline_reason']
        self.decline_detail = decline['decline_text']
        self.decline_advice = decline['decline_advice']

    @staticmethod
    def get_all_decline_reasons():
        return DeclineReason.query.filter_by(date_ended=None).order_by(asc(DeclineReason.decline_id)).all()

    def as_dict(self):
        return {
            'decline_id': self.decline_id,
            'decline_description': self.decline_description,
            'decline_detail': self.decline_detail,
            'decline_advice': self.decline_advice,
            'date_added': str(self.date_added),
            'date_ended': str(self.date_ended)
        }


class Close(db.Model):
    __tablename__ = 'close'
    close_id = db.Column(db.Integer, primary_key=True)
    verification_id = db.Column(db.Integer, db.ForeignKey('verification.verification_id'), nullable=False)
    close_detail = db.Column(db.String, nullable=False)
    requester = db.Column(db.String, nullable=False)
    staff_id = db.Column(db.String, nullable=True)
    date_added = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __init__(self, case_id, closure):
        self.verification_id = case_id
        self.close_detail = closure['close_detail']
        self.requester = closure['requester']
        self.staff_id = closure['staff_id']

    @staticmethod
    def get_closure_by_case_id(case_id):
        return Close.query.filter_by(verification_id=case_id).first()
