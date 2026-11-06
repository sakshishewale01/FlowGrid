"""add vehicle maintenance records

Revision ID: 9a6f2d8e1c44
Revises: b7d8e9f0a1b2
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a6f2d8e1c44"
down_revision: Union[str, Sequence[str], None] = "b7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicle_maintenance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("service_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="SCHEDULED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicle_maintenance_vehicle_id", "vehicle_maintenance", ["vehicle_id"])
    op.create_index("ix_vehicle_maintenance_scheduled_date", "vehicle_maintenance", ["scheduled_date"])
    op.create_index("ix_vehicle_maintenance_status", "vehicle_maintenance", ["status"])


def downgrade() -> None:
    op.drop_index("ix_vehicle_maintenance_status", table_name="vehicle_maintenance")
    op.drop_index("ix_vehicle_maintenance_scheduled_date", table_name="vehicle_maintenance")
    op.drop_index("ix_vehicle_maintenance_vehicle_id", table_name="vehicle_maintenance")
    op.drop_table("vehicle_maintenance")
