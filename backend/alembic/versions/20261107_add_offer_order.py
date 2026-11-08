"""Persist offer display order."""

from alembic import op
import sqlalchemy as sa


revision = "20261107_offer_order"
down_revision = "20261029_category_order"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "Ofertas",
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
    )
    connection = op.get_bind()
    offer_ids = connection.execute(
        sa.text('SELECT id FROM "Ofertas" ORDER BY fecha_creacion, id')
    ).scalars()
    for order, offer_id in enumerate(offer_ids):
        connection.execute(
            sa.text('UPDATE "Ofertas" SET orden = :orden WHERE id = :id'),
            {"orden": order, "id": offer_id},
        )


def downgrade() -> None:
    op.drop_column("Ofertas", "orden")
