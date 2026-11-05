"""create delivery confirmations

Revision ID: b7d8e9f0a1b2
Revises: a1c2d3e4f5a6
Create Date: 2026-11-05 15:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_confirmations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("shipment_id", sa.Integer(), nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=False),
        sa.Column("recipient_name", sa.String(length=150), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_notes", sa.Text(), nullable=True),
        sa.Column("evidence_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["shipment_id"],
            ["shipments.id"],
            name="fk_delivery_confirmations_shipment_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"],
            ["users.id"],
            name="fk_delivery_confirmations_submitted_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shipment_id", name="uq_delivery_confirmations_shipment_id"),
    )
    op.create_index(
        "ix_delivery_confirmations_shipment_id",
        "delivery_confirmations",
        ["shipment_id"],
    )
    op.create_index(
        "ix_delivery_confirmations_submitted_by_user_id",
        "delivery_confirmations",
        ["submitted_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_delivery_confirmations_submitted_by_user_id",
        table_name="delivery_confirmations",
    )
    op.drop_index(
        "ix_delivery_confirmations_shipment_id",
        table_name="delivery_confirmations",
    )
    op.drop_table("delivery_confirmations")
