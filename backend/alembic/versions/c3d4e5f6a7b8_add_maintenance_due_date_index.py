"""add maintenance due date index

Revision ID: c3d4e5f6a7b8
Revises: a2b3c4d5e6f7
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_vehicle_maintenance_next_service_due_date",
        "vehicle_maintenance",
        ["next_service_due_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vehicle_maintenance_next_service_due_date",
        table_name="vehicle_maintenance",
    )
