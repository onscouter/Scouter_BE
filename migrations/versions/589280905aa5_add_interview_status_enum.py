"""add interview status enum

Revision ID: 589280905aa5
Revises: 7bcfd08a479f
Create Date: 2025-09-01 15:26:37.821838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '589280905aa5'
down_revision: Union[str, None] = '7bcfd08a479f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the new enum type
    interview_status_enum = sa.Enum(
        'NOT_SCHEDULED',
        'SCHEDULED',
        'RESCHEDULED',
        'CANCELLED',
        'COMPLETED',
        'NO_SHOW',
        'FEEDBACK_PENDING',
        name='interview_status_enum'  # ✅ NEW ENUM NAME
    )
    interview_status_enum.create(op.get_bind())

    # Add the new column using the new enum
    op.add_column(
        'job_interviews',
        sa.Column(
            'interview_status',
            interview_status_enum,
            server_default=sa.text("'NOT_SCHEDULED'"),
            nullable=False
        )
    )

    op.create_index(
        op.f('ix_job_interviews_interview_status'),
        'job_interviews',
        ['interview_status'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_job_interviews_interview_status'), table_name='job_interviews')
    op.drop_column('job_interviews', 'interview_status')

    # Drop the enum type from Postgres
    sa.Enum(name='interview_status_enum').drop(op.get_bind())
