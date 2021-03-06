"""Add decline_advice column and repopulate the table

Revision ID: 594dc4410fc6
Revises: f6ad23a1bfef
Create Date: 2020-02-05 13:42:58.515770

"""
from alembic import op
import sqlalchemy as sa
import datetime


# revision identifiers, used by Alembic.
revision = '594dc4410fc6'
down_revision = 'f6ad23a1bfef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    delete_sql = "DELETE from decline_reason"
    op.execute(delete_sql)

    op.add_column('decline_reason', sa.Column('decline_advice', sa.String(), nullable=False))

    insert_sql = "INSERT into decline_reason (decline_description, decline_detail, date_added, decline_advice) VALUES('{}','{}','{}', '{}')"
    reasons = [
        {"reason": "Company not found on Companies House",
         "text": "Your company name or number was not found on Companies House records.",
         "advice": "If the company is registered overseas, you need to create an account for an overseas "
                   "organisation.\r\n\r\nIf it''s a UK company but does not have a company registration number, "
                   "reapply for an account requesting access to the data for your own use."},
        {"reason": "Company Registration Number does not match the registration number on the Companies House website",
         "text": "Your company name and number do not match Companies House records.​​",
         "advice": "Reapply using the correct company name or number.\r\n\r\nIf the company is registered "
                   "overseas, you need to create an account for an overseas organisation."},
        {"reason": "Company switchboard has no knowledge of applicant",
         "text": "We checked the details you gave, and we cannot verify your connection with the company,​",
         "advice": "Reapply for an account requesting access to the data for your own use."},
        {"reason": "Charity cannot be found on the CC website",
         "text": "Your charity could not be found on Charity Commission records.​​",
         "advice": "If the charity is registered in the UK, reapply and enter the charity number.​\r\n\r\nIf you "
                   "do not have a registered charity number, reapply for an account requesting access to the "
                   "data for your own use.​"},
        {"reason": "Charity Registration number​ does not match",
         "text": "Your charity name and charity number do not match the Charity Commission records.​​",
         "advice": "Reapply using the correct charity name and number​.\r\n\r\nIf you are an exempt charity or you "
                   "cannot supply these details, reapply for an account requesting access to the data for "
                   "your own use.​"}
    ]

    for rows in reasons:
        op.execute(insert_sql.format(rows['reason'], rows['text'], datetime.datetime.utcnow(), rows['advice']))
    pass
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('decline_reason', 'decline_advice')
    # ### end Alembic commands ###
