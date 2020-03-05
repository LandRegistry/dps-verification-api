"""close table

Revision ID: f6ad23a1bfef
Revises: d583d26ef996
Create Date: 2019-05-15 15:18:51.680607

"""
from alembic import op
import sqlalchemy as sa
from flask import current_app


# revision identifiers, used by Alembic.
revision = 'f6ad23a1bfef'
down_revision = 'd583d26ef996'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('close',
                    sa.Column('close_id', sa.Integer(), nullable=False),
                    sa.Column('verification_id', sa.Integer(), nullable=False),
                    sa.Column('close_detail', sa.String(), nullable=False),
                    sa.Column('staff_id', sa.String(), nullable=True),
                    sa.Column('requester', sa.String(), nullable=False),
                    sa.Column('date_added', sa.DateTime(timezone=True), nullable=True),
                    sa.ForeignKeyConstraint(['verification_id'], ['verification.verification_id'], ),
                    sa.PrimaryKeyConstraint('close_id')
                    )
    op.execute("GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE close TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT USAGE, SELECT ON close_close_id_seq TO " + current_app.config.get('APP_SQL_USERNAME'))


def downgrade():
    op.drop_table('close')
