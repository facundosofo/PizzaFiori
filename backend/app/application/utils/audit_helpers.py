"""
Helpers para generar diffs de entidades para auditoría.
"""
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from decimal import Decimal

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty


# Campos sensibles que no deben incluirse en auditoría por seguridad
SENSITIVE_FIELDS = {
    'password_hash',
    'password',
    'token',
    'refresh_token',
    'api_key',
    'secret_key',
}


def compute_entity_diff(
    old_entity: Any,
    new_entity: Any,
    exclude_fields: Optional[Set[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Compara dos instancias de la misma entidad y retorna un diccionario
    con los campos que cambiaron.
    
    Args:
        old_entity: Instancia anterior de la entidad
        new_entity: Instancia nueva de la entidad
        exclude_fields: Set de nombres de campos a excluir del diff
    
    Returns:
        Diccionario con formato: {"field_name": {"old": valor_anterior, "new": valor_nuevo}}
        Solo incluye campos que realmente cambiaron.
    
    Example:
        >>> old_product = Product(nombre="Pizza", precio=100)
        >>> new_product = Product(nombre="Pizza Deluxe", precio=150)
        >>> diff = compute_entity_diff(old_product, new_product)
        >>> # {"nombre": {"old": "Pizza", "new": "Pizza Deluxe"}, "precio": {"old": 100, "new": 150}}
    """
    if exclude_fields is None:
        # Excluir automáticamente campos de timestamp y campos sensibles
        exclude_fields = {
            'fecha_actualizacion', 
            'updated_at', 
            'fecha_creacion',
            'created_at',
        }.union(SENSITIVE_FIELDS)
    else:
        # Si se pasan exclude_fields, agregar los campos sensibles al conjunto
        exclude_fields = exclude_fields.union(SENSITIVE_FIELDS)
    
    diff = {}
    
    # Obtener mapper de SQLAlchemy para la entidad
    mapper = inspect(old_entity.__class__)
    
    for column in mapper.columns:
        field_name = column.name
        
        # Saltar campos excluidos
        if field_name in exclude_fields:
            continue
        
        old_value = getattr(old_entity, field_name, None)
        new_value = getattr(new_entity, field_name, None)
        
        # Normalizar valores para comparación
        old_value_normalized = _normalize_value(old_value)
        new_value_normalized = _normalize_value(new_value)
        
        # Solo incluir si cambió
        if old_value_normalized != new_value_normalized:
            diff[field_name] = {
                "old": old_value_normalized,
                "new": new_value_normalized,
            }
    
    return diff


def compute_sale_diff(old_sale: Any, new_sale: Any) -> Dict[str, Any]:
    """
    Genera un diff especializado para ventas, incluyendo comparación de items.
    
    Args:
        old_sale: Instancia anterior de Sale
        new_sale: Instancia nueva de Sale
    
    Returns:
        Diccionario con cambios en la venta y sus items
    """
    # Diff de campos básicos de la venta
    basic_diff = compute_entity_diff(old_sale, new_sale)
    
    # Comparar items de la venta
    old_items = {item.id: item for item in getattr(old_sale, 'items', [])}
    new_items = {item.id: item for item in getattr(new_sale, 'items', [])}
    
    items_diff = {
        "items_added": [],
        "items_removed": [],
        "items_modified": [],
    }
    
    # Items eliminados
    for item_id in set(old_items.keys()) - set(new_items.keys()):
        items_diff["items_removed"].append({
            "id": item_id,
            "data": _serialize_sale_item(old_items[item_id]),
        })
    
    # Items agregados
    for item_id in set(new_items.keys()) - set(old_items.keys()):
        items_diff["items_added"].append({
            "id": item_id,
            "data": _serialize_sale_item(new_items[item_id]),
        })
    
    # Items modificados
    for item_id in set(old_items.keys()) & set(new_items.keys()):
        item_diff = compute_entity_diff(old_items[item_id], new_items[item_id])
        if item_diff:  # Solo si hay cambios
            items_diff["items_modified"].append({
                "id": item_id,
                "changes": item_diff,
            })
    
    # Combinar diff básico con diff de items
    if any(items_diff.values()):  # Si hay cambios en items
        basic_diff["items"] = items_diff
    
    return basic_diff


def entity_to_snapshot(entity: Any, exclude_fields: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Convierte una entidad a un snapshot (diccionario) para auditoría.
    Útil para registrar el estado completo en CREATE o DELETE.
    
    Args:
        entity: Instancia de la entidad
        exclude_fields: Set de nombres de campos a excluir
    
    Returns:
        Diccionario con todos los campos de la entidad (excepto sensibles)
    """
    if exclude_fields is None:
        # Excluir campos de timestamp y campos sensibles por seguridad
        exclude_fields = {
            'fecha_actualizacion', 
            'updated_at', 
            'fecha_creacion',
            'created_at',
        }.union(SENSITIVE_FIELDS)
    else:
        # Si se pasan exclude_fields, agregar los campos sensibles al conjunto
        exclude_fields = exclude_fields.union(SENSITIVE_FIELDS)
    
    snapshot = {}
    mapper = inspect(entity.__class__)
    
    for column in mapper.columns:
        field_name = column.name
        
        if field_name in exclude_fields:
            continue
        
        value = getattr(entity, field_name, None)
        snapshot[field_name] = _normalize_value(value)
    
    return snapshot


def sale_to_snapshot(sale: Any) -> Dict[str, Any]:
    """
    Convierte una venta a un snapshot completo incluyendo sus items.
    
    Args:
        sale: Instancia de Sale
    
    Returns:
        Diccionario con la venta y todos sus items
    """
    snapshot = entity_to_snapshot(sale)
    
    # Agregar items si existen
    items = getattr(sale, 'items', [])
    if items:
        snapshot["items"] = [_serialize_sale_item(item) for item in items]
    
    return snapshot


def _serialize_sale_item(item: Any) -> Dict[str, Any]:
    """
    Serializa un SaleItem a diccionario para el snapshot.
    """
    return {
        "id": item.id,
        "producto_id": item.producto_id,
        "oferta_id": item.oferta_id,
        "cantidad": item.cantidad,
        "precio_unitario": _normalize_value(item.precio_unitario),
        "subtotal": _normalize_value(item.subtotal),
        "producto_sku": item.producto_sku,
        "item_nombre": item.item_nombre,
        "item_categoria": item.item_categoria,
        "item_descripcion": item.item_descripcion,
        "es_pizza_mitad_mitad": item.es_pizza_mitad_mitad,
    }


def _normalize_value(value: Any) -> Any:
    """
    Normaliza valores para comparación y serialización JSON.
    
    - datetime -> ISO string
    - Decimal -> float
    - None -> None
    - Otros -> tal cual
    """
    if value is None:
        return None
    
    if isinstance(value, datetime):
        return value.isoformat()
    
    if isinstance(value, Decimal):
        return float(value)
    
    if isinstance(value, (int, float, str, bool)):
        return value
    
    # Para otros tipos, convertir a string
    return str(value)
