"""Add dashboard optimization indexes

Revision ID: add_dashboard_indexes
Revises: f7ed2d406c50
Create Date: 2026-02-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_dashboard_indexes'
down_revision: Union[str, Sequence[str], None] = 'f7ed2d406c50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes to optimize dashboard queries."""
    
    # Sale: índice en fecha_creacion para filtros de rango de fechas
    op.create_index('ix_Ventas_fecha_creacion', 'Ventas', ['fecha_creacion'])
    
    # SaleItem: índices compuestos para JOINs y filtros
    op.create_index('ix_ventaitems_venta_producto', 'VentaItems', ['venta_id', 'producto_id'])
    op.create_index('ix_ventaitems_venta_oferta', 'VentaItems', ['venta_id', 'oferta_id'])
    op.create_index('ix_ventaitems_item_categoria', 'VentaItems', ['item_categoria'])
    
    # SaleItemOfferProduct: índices para agregaciones de productos en ofertas
    op.create_index('ix_ventaitemofertaproductos_ventaitem_producto', 'VentaItemOfertaProductos', ['venta_item_id', 'producto_id'])
    op.create_index('ix_ventaitemofertaproductos_categoria_nombre', 'VentaItemOfertaProductos', ['categoria_nombre'])
    op.create_index('ix_ventaitemofertaproductos_producto_nombre', 'VentaItemOfertaProductos', ['producto_nombre'])
    
    # Product: índice en categoria_id para JOINs con Category
    op.create_index('ix_productos_categoria', 'Productos', ['categoria_id'])
    
    # ProductPrice: índice compuesto para búsquedas de precio por cantidad
    op.create_index('ix_productoprecio_producto_cantidad', 'ProductoPrecios', ['producto_id', 'cantidad'])


def downgrade() -> None:
    """Remove dashboard optimization indexes."""
    
    # Eliminar índices en orden inverso
    op.drop_index('ix_productoprecio_producto_cantidad', table_name='ProductoPrecios')
    op.drop_index('ix_productos_categoria', table_name='Productos')
    op.drop_index('ix_ventaitemofertaproductos_producto_nombre', table_name='VentaItemOfertaProductos')
    op.drop_index('ix_ventaitemofertaproductos_categoria_nombre', table_name='VentaItemOfertaProductos')
    op.drop_index('ix_ventaitemofertaproductos_ventaitem_producto', table_name='VentaItemOfertaProductos')
    op.drop_index('ix_ventaitems_item_categoria', table_name='VentaItems')
    op.drop_index('ix_ventaitems_venta_oferta', table_name='VentaItems')
    op.drop_index('ix_ventaitems_venta_producto', table_name='VentaItems')
    op.drop_index('ix_Ventas_fecha_creacion', table_name='Ventas')
