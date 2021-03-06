"""Initial Database

Revision ID: 1cf8fab46a0c
Revises:
Create Date: 2019-03-07 09:08:01.830970

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from flask import current_app

# revision identifiers, used by Alembic.
revision = '1cf8fab46a0c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('decline_reason',
    sa.Column('decline_id', sa.Integer(), nullable=False),
    sa.Column('decline_description', sa.String(), nullable=False),
    sa.Column('decline_detail', sa.String(), nullable=False),
    sa.Column('date_added', sa.DateTime(timezone=True), nullable=True),
    sa.Column('date_ended', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('decline_id')
    )
    op.execute("GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE decline_reason TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT USAGE, SELECT ON decline_reason_decline_id_seq TO " + current_app.config.get('APP_SQL_USERNAME'))

    op.create_table('verification',
    sa.Column('verification_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('ldap_id', sa.String(), nullable=False),
    sa.Column('registration_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('date_added', sa.DateTime(timezone=True), nullable=True),
    sa.Column('staff_id', sa.String(), nullable=True),
    sa.Column('date_agreed', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('verification_id')
    )
    op.execute("GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE verification TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT USAGE, SELECT ON verification_verification_id_seq TO " + current_app.config.get('APP_SQL_USERNAME'))

    op.create_table('note',
    sa.Column('note_id', sa.Integer(), nullable=False),
    sa.Column('verification_id', sa.Integer(), nullable=False),
    sa.Column('note_detail', sa.String(), nullable=False),
    sa.Column('staff_id', sa.String(), nullable=True),
    sa.Column('date_added', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['verification_id'], ['verification.verification_id'], ),
    sa.PrimaryKeyConstraint('note_id')
    )
    op.execute("GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE note TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT USAGE, SELECT ON note_note_id_seq TO " + current_app.config.get('APP_SQL_USERNAME'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('note')
    op.drop_table('verification')
    op.drop_table('decline_reason')
    # ### end Alembic commands ###
