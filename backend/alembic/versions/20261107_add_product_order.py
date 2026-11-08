"""Persist product display order within each category."""

from alembic import op
import sqlalchemy as sa


revision = "20261107_product_order"
down_revision = "20261107_offer_order"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "Productos",
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
    )
    connection = op.get_bind()
    products = connection.execute(
        sa.text('SELECT id, categoria_id FROM "Productos" ORDER BY categoria_id, id')
    )
    category_orders = {}
    for product_id, category_id in products:
        order = category_orders.get(category_id, 0)
        connection.execute(
            sa.text('UPDATE "Productos" SET orden = :orden WHERE id = :id'),
            {"orden": order, "id": product_id},
        )
        category_orders[category_id] = order + 1


def downgrade() -> None:
    op.drop_column("Productos", "orden")
