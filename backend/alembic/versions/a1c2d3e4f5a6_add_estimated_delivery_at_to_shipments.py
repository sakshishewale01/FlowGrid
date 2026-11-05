"""add estimated_delivery_at to shipments

Revision ID: a1c2d3e4f5a6
Revises: 9090bc4b1426
Create Date: 2026-11-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "9090bc4b1426"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the nullable promised-delivery timestamp."""
    op.add_column(
        "shipments",
        sa.Column("estimated_delivery_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove the promised-delivery timestamp."""
    op.drop_column("shipments", "estimated_delivery_at")
