"""Persist product category display order."""

from alembic import op
import sqlalchemy as sa


revision = "20261029_category_order"
down_revision = "20260703_offer_items_qty"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "productos_categorias",
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
    )
    connection = op.get_bind()
    category_ids = connection.execute(
        sa.text("SELECT id FROM productos_categorias ORDER BY id")
    ).scalars()
    for order, category_id in enumerate(category_ids):
        connection.execute(
            sa.text("UPDATE productos_categorias SET orden = :orden WHERE id = :id"),
            {"orden": order, "id": category_id},
        )


def downgrade() -> None:
    op.drop_column("productos_categorias", "orden")
