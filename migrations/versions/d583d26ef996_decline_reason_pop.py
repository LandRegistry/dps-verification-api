"""Populate decline_reason

Revision ID: d583d26ef996
Revises: 1cf8fab46a0c
Create Date: 2019-03-07 09:23:18.830141

"""
from alembic import op
import datetime


# revision identifiers, used by Alembic.
revision = 'd583d26ef996'
down_revision = '1cf8fab46a0c'
branch_labels = None
depends_on = None


def upgrade():
    insert_sql = "INSERT into decline_reason (decline_description, decline_detail, date_added) VALUES('{}','{}','{}')"
    reasons = [
        {'reason': 'Company not found on Companies House',
         'text': 'Following a check we have made with Companies House it appears that your company name/number could '
                 'not be found on their records. If the company is registered overseas please, reapply ensuring the '
                 'correct ‘User Type’ is selected when reapplying.'},
        {'reason': 'Company Registration Number does not match the registration number on the Companies House website',
         'text': 'Following a check we have made with Companies House it appears that your company name and number '
                 'do not match their records. Please, therefore, reapply using the correct company name/number.'},
        {'reason': 'Company switchboard has no knowledge of applicant',
         'text': 'Following a check, we cannot verify your connection with the Corporate Body stated.'},
        {'reason': 'Charity cannot be found on the CC website',
         'text': 'Following a check we have made with Charity Commission, your charity could not be found on '
                 'their records. If the charity is registered in the UK, please reapply ensuring the charity number '
                 'is quoted.'},
        {'reason': 'Charity Registration number​ does not match',
         'text': 'Following a check we have made with the Charity Commission, it appears that your charity name '
                 'and charity number do not match their records. Please, therefore, reapply using the correct '
                 'charity name/number.'}
    ]

    for rows in reasons:
        op.execute(insert_sql.format(rows['reason'], rows['text'], datetime.datetime.utcnow()))
    pass


def downgrade():
    pass
