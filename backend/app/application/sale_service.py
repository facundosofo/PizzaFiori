from dataclasses import dataclass
import re
from typing import Optional, List
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import structlog

from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.models.sale_item_offer_product import SaleItemOfferProduct
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.sale_schemas import SaleCreateRequest


@dataclass
class ServiceResult:
    value: Optional[Sale | List[Sale]] = None
    error: Optional[str] = None
    status_code: int = 200


class SaleService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        audit_service=None,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.audit_service = audit_service
        self.logger = logger or structlog.get_logger(__name__)

    def limpiar_nombre_pizza(self,nombre: str) -> str:
        """
        Elimina 'pizza', 'pizza de' o 'pizza con' del inicio del nombre.
        Case-insensitive.
        """
        if not nombre:
            return ""
        return re.sub(r"^pizza(\s+(de|con))?\s*", "", nombre, flags=re.IGNORECASE).strip()

    def _get_product_price(self, producto, cantidad: int) -> Optional[Decimal]:
        """
        Calcula el precio total usando sistema de rangos.
        
        Ejemplo: Si compras 7 empanadas con precios:
        - 1 unidad: $1200
        - 6 unidades: $6000
        - 12 unidades: $10800
        
        Cálculo para 7:
        - Primeras 6 al precio de 6: $6000
        - La 7ma al precio de 1: $1200
        - Total: $7200
        
        Retorna el precio TOTAL (no unitario), que luego se divide por la cantidad
        para obtener el precio_unitario en la venta.
        """
        if not producto or not producto.activo:
            return None
        
        if not producto.precios:
            return None
        
        # Ordenar precios por cantidad descendente
        precios_ordenados = sorted(producto.precios, key=lambda p: p.cantidad, reverse=True)
        
        cantidad_restante = cantidad
        precio_total = Decimal("0.00")
        
        # Aplicar rangos de mayor a menor
        for rango_precio in precios_ordenados:
            if cantidad_restante >= rango_precio.cantidad:
                # Cuántas veces entra este rango completo
                veces = cantidad_restante // rango_precio.cantidad
                precio_total += rango_precio.precio * veces
                cantidad_restante = cantidad_restante % rango_precio.cantidad
                
                if cantidad_restante == 0:
                    break
        
        # Si quedan unidades, aplicar el precio del rango más pequeño
        if cantidad_restante > 0:
            precio_minimo = min(precios_ordenados, key=lambda p: p.cantidad)
            # Calcular precio unitario del rango más pequeño
            precio_unitario_minimo = precio_minimo.precio / precio_minimo.cantidad
            precio_total += precio_unitario_minimo * cantidad_restante
        
        # Retornar precio unitario promedio (para mantener compatibilidad con el resto del código)
        return precio_total / cantidad

    def _get_offer_price(self, oferta) -> Optional[Decimal]:
        """Obtiene el precio de una oferta."""
        if not oferta or not oferta.activo:
            return None
        
        return oferta.precio

    async def _validate_offer_products(self, oferta, productos_seleccionados, uow) -> Optional[ServiceResult]:
        """
        Valida que los productos seleccionados cumplan con los requisitos de la oferta.
        
        Para cada OfferItem de la oferta, verifica que:
        - Si tiene UN producto específico: el cliente debe seleccionar ese producto exacto
          con la cantidad requerida
        - Si tiene opciones múltiples (varios productos): el cliente debe elegir UNO de ellos
          con la cantidad exacta requerida. Ejemplo: "6 empanadas de: jamón, carne o pollo"
          → el cliente elige 6 de jamón, o 6 de carne, o 6 de pollo (no puede combinar)
        - Si tiene categoría: el cliente puede combinar varios productos de esa categoría
          sumando cantidades hasta alcanzar la cantidad requerida
        - Las cantidades coincidan exactamente con lo requerido
        - No se reutilicen productos entre diferentes OfferItems
        - No se envíen productos extra que no pertenezcan a ningún item
        
        Args:
            oferta: La oferta que se está validando
            productos_seleccionados: Lista de productos seleccionados por el cliente
            uow: Unit of Work para acceder a repositorios
            
        Returns:
            ServiceResult con error si la validación falla, None si es exitosa
        """
        # Convertir lista de productos seleccionados a diccionario para búsqueda rápida
        productos_seleccionados_validados = {}
        for prod_sel in productos_seleccionados:
            productos_seleccionados_validados[prod_sel.producto_id] = prod_sel.cantidad
        
        # Mapeo de productos ya utilizados para evitar duplicados entre OfferItems
        productos_usados = set()
        
        # Verificar cada OfferItem de la oferta
        for oferta_item in oferta.productos:
            cantidad_requerida = oferta_item.cantidad
            cantidad_seleccionada = 0
            productos_de_este_item = []
            
            # Caso 1: OfferItem con producto(s) específico(s)
            # - Un producto: el cliente debe seleccionar ese producto con la cantidad exacta
            # - Opciones múltiples: el cliente debe elegir UNO de ellos con la cantidad exacta
            # Ejemplo: "6 empanadas de: jamón, carne o pollo" → elegir 6 de UNO solo
            if oferta_item.productos:
                productos_permitidos_ids = [p.id for p in oferta_item.productos]
                
                # Buscar producto seleccionado de la lista permitida
                # Solo se permite elegir UNO de los productos disponibles
                for prod_id, cantidad in productos_seleccionados_validados.items():
                    if prod_id in productos_permitidos_ids and prod_id not in productos_usados:
                        productos_de_este_item.append(prod_id)
                        cantidad_seleccionada = cantidad
                        productos_usados.add(prod_id)
                        break
                
                if not productos_de_este_item:
                    productos_nombres = [p.nombre for p in oferta_item.productos]
                    return ServiceResult(
                        error=f"La oferta '{oferta.nombre}' requiere seleccionar {cantidad_requerida} de: {', '.join(productos_nombres)}",
                        status_code=400,
                    )
            
            # Caso 2: OfferItem con categoría (permite combinar productos)
            # El cliente puede seleccionar varios productos de la categoría
            # y sumar sus cantidades hasta alcanzar la cantidad requerida
            # Ejemplo: "6 empanadas" → 2 jamón + 2 carne + 2 pollo = 6 ✓
            elif oferta_item.categoria_id:
                # Buscar TODOS los productos seleccionados de la categoría correcta
                for prod_id, cantidad in productos_seleccionados_validados.items():
                    if prod_id not in productos_usados:
                        # Obtener el producto para verificar su categoría
                        producto_temp = await uow.product_repo.get_by_id(prod_id)
                        if producto_temp and producto_temp.categoria_id == oferta_item.categoria_id:
                            productos_de_este_item.append(prod_id)
                            cantidad_seleccionada += cantidad
                            productos_usados.add(prod_id)
                
                if not productos_de_este_item:
                    categoria_nombre = oferta_item.categoria_nombre or f"categoría {oferta_item.categoria_id}"
                    return ServiceResult(
                        error=f"La oferta '{oferta.nombre}' requiere seleccionar {cantidad_requerida} de la categoría: {categoria_nombre}",
                        status_code=400,
                    )
            
            # Validar que la cantidad coincida
            if cantidad_seleccionada != cantidad_requerida:
                return ServiceResult(
                    error=f"La oferta '{oferta.nombre}' requiere {cantidad_requerida} unidades, pero se enviaron {cantidad_seleccionada}",
                    status_code=400,
                )
        
        # Validar que no se enviaron productos extra que no se usaron
        productos_no_usados = set(productos_seleccionados_validados.keys()) - productos_usados
        if productos_no_usados:
            return ServiceResult(
                error=f"Se enviaron productos que no pertenecen a ningún item de la oferta '{oferta.nombre}'",
                status_code=400,
            )
        
        # Validación exitosa
        return None

    async def create(
        self, 
        sale_create: SaleCreateRequest,
        username: Optional[str] = None,
    ) -> ServiceResult:
        """Crea una nueva venta."""
        try:
            self.logger.debug(
                "Creando venta",
                items_count=len(sale_create.items),
            )

            sale_items = []
            total = Decimal("0.00")

            async with self.uow as uow:
                # Siempre generar `numero_orden` - ahora es obligatorio y auto-generado
                now = datetime.now()
                # Ajuste de fecha de negocio (-6 horas) para que las ventas
                # entre 00:00-05:59 se asignen al día anterior
                business_dt = now - timedelta(hours=6)
                business_date = business_dt.date()

                # Generación atómica usando tabla de secuencia diaria
                sequence = await uow.sequence_repo.get_for_update(business_date)
                if not sequence:
                    seq = 1
                    await uow.sequence_repo.create(business_date, seq)
                else:
                    sequence.last_value += 1
                    seq = sequence.last_value
                    await uow.sequence_repo.update(sequence)

                if seq > 99999:
                    return ServiceResult(
                        error="Secuencia diaria de números de orden excedida",
                        status_code=500,
                    )

                numero_orden_val = f"#ORD-{business_date.strftime('%y%m%d')}-{seq:05d}"
                # dict para acumular descuentos de stock por categoria: {categoria_id: delta}
                stock_deductions: dict[int, int] = {}
                # dict para acumular descuentos de stock por producto: {producto_id: delta}
                product_stock_deductions: dict[int, int] = {}
                # map producto_id -> categoria_id para evitar re-fetch en el loop de descuento
                producto_categoria_ids: dict[int, int] = {}
                # Validar y calcular precios para cada item
                for item in sale_create.items:
                    precio_unitario = None
                    item_nombre = None
                    item_descripcion = None
                    item_categoria = None
                    producto_sku = None
                    oferta_productos_snapshot = []
                    
                    if item.producto_id:
                        # Validar que el producto existe y está activo
                        producto = await uow.product_repo.get_by_id(item.producto_id)
                        if not producto:
                            return ServiceResult(
                                error=f"Producto {item.producto_id} no encontrado",
                                status_code=404,
                            )
                        
                        # Obtener precio según cantidad
                        precio_unitario = self._get_product_price(producto, item.cantidad)
                        if precio_unitario is None:
                            return ServiceResult(
                                error=f"No se pudo obtener el precio para el producto {item.producto_id} con cantidad {item.cantidad}",
                                status_code=400,
                            )
                        
                        # Guardar snapshot del producto
                        item_nombre = producto.nombre
                        producto_sku = producto.sku
                        item_categoria = producto.categoria.nombre if producto.categoria else 'Sin categoría'
                        if producto.categoria_id:
                            stock_deductions[producto.categoria_id] = (
                                stock_deductions.get(producto.categoria_id, 0) + item.cantidad
                            )
                        product_stock_deductions[item.producto_id] = (
                            product_stock_deductions.get(item.producto_id, 0) + item.cantidad
                        )
                        if producto.categoria_id:
                            producto_categoria_ids[item.producto_id] = producto.categoria_id
                    
                    elif item.oferta_id:
                        # Validar que la oferta existe y está activa
                        oferta = await uow.offer_repo.get_by_id(item.oferta_id)
                        if not oferta:
                            return ServiceResult(
                                error=f"Oferta {item.oferta_id} no encontrada",
                                status_code=404,
                            )
                        
                        # Obtener precio de la oferta
                        precio_unitario = self._get_offer_price(oferta)
                        if precio_unitario is None:
                            return ServiceResult(
                                error=f"No se pudo obtener el precio para la oferta {item.oferta_id}",
                                status_code=400,
                            )
                        
                        # Guardar snapshot de la oferta
                        item_nombre = oferta.nombre
                        item_descripcion = oferta.descripcion
                        item_categoria = 'Ofertas'
                        
                        # Validar productos seleccionados contra requisitos de la oferta
                        validation_error = await self._validate_offer_products(
                            oferta, 
                            item.productos_seleccionados, 
                            uow
                        )
                        if validation_error:
                            return validation_error
                        
                        # Crear snapshot de los productos que el cliente seleccionó
                        if item.productos_seleccionados:
                            for prod_sel in item.productos_seleccionados:
                                # Obtener el producto para hacer el snapshot
                                producto = await uow.product_repo.get_by_id(prod_sel.producto_id)
                                if not producto:
                                    return ServiceResult(
                                        error=f"Producto {prod_sel.producto_id} en productos_seleccionados no encontrado",
                                        status_code=404,
                                    )
                                
                                snapshot = SaleItemOfferProduct(
                                    producto_id=producto.id,
                                    producto_nombre=producto.nombre,
                                    categoria_nombre=producto.categoria.nombre if producto.categoria else 'Sin categoría',
                                    cantidad=prod_sel.cantidad
                                )
                                oferta_productos_snapshot.append(snapshot)
                                # Acumular descuento de stock para la categoría del producto en la oferta
                                if producto.categoria_id:
                                    deduccion_total = prod_sel.cantidad * item.cantidad
                                    stock_deductions[producto.categoria_id] = (
                                        stock_deductions.get(producto.categoria_id, 0) + deduccion_total
                                    )
                                    product_stock_deductions[prod_sel.producto_id] = (
                                        product_stock_deductions.get(prod_sel.producto_id, 0) + deduccion_total
                                    )
                                    producto_categoria_ids[prod_sel.producto_id] = producto.categoria_id
                    
                    elif item.pizza_mitad_mitad:
                        # Validar y procesar pizza mitad-mitad
                        validation_error = await self._validate_pizza_mitad_mitad(
                            item.pizza_mitad_mitad, uow
                        )
                        if validation_error:
                            return validation_error
                        
                        # Obtener productos y calcular precio
                        producto_izq = await uow.product_repo.get_by_id(item.pizza_mitad_mitad.producto_id_izquierda)
                        producto_der = await uow.product_repo.get_by_id(item.pizza_mitad_mitad.producto_id_derecha)
                        
                        # Calcular precio (el de la pizza más cara)
                        precio_unitario = self._get_pizza_mitad_mitad_price(producto_izq, producto_der)
                        if precio_unitario is None:
                            return ServiceResult(
                                error="No se pudo calcular el precio para la pizza mitad-mitad",
                                status_code=400,
                            )
                        
                        # Generar nombre completo y guardar snapshot
                        nombre1 = self.limpiar_nombre_pizza(producto_izq.nombre)
                        nombre2 = self.limpiar_nombre_pizza(producto_der.nombre)
                        item_nombre = f"Pizza Mitad {nombre1}/{nombre2}"
                        item_categoria = "Pizzas"
                        item_descripcion = f"Pizza Mitad {nombre1}/{nombre2}"
                        pizza_cat_id = (
                            producto_izq.categoria_id if producto_izq and producto_izq.categoria_id
                            else (producto_der.categoria_id if producto_der else None)
                        )
                        if pizza_cat_id:
                            stock_deductions[pizza_cat_id] = (
                                stock_deductions.get(pizza_cat_id, 0) + item.cantidad
                            )
                    
                    # Calcular subtotal
                    subtotal = Decimal(str(precio_unitario)) * Decimal(str(item.cantidad))
                    total += subtotal
                    
                    sale_item = SaleItem(
                        producto_id=item.producto_id,
                        oferta_id=item.oferta_id,
                        cantidad=item.cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal,
                        # Referencia de negocio (solo productos tienen SKU)
                        producto_sku=producto_sku,
                        # Snapshot completo
                        item_nombre=item_nombre,
                        item_categoria=item_categoria,
                        item_descripcion=item_descripcion,
                        # Identificador de pizza mitad-mitad
                        es_pizza_mitad_mitad=bool(item.pizza_mitad_mitad),
                        oferta_productos_snapshot=oferta_productos_snapshot
                    )
                    sale_items.append(sale_item)

                sale = Sale(
                    numero_orden=numero_orden_val,
                    total=total,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                    items=sale_items,
                )

                await uow.sale_repo.add(sale)

                # Descontar stock por categoria para todos los items de la venta
                from datetime import datetime as _dt

                # Determinar qué categorías usan stock por producto
                cats_por_producto: set[int] = set()
                for cat_id in stock_deductions:
                    cat_obj = await uow.product_category_repo.get_by_id(cat_id)
                    if cat_obj and cat_obj.stock_por_producto:
                        cats_por_producto.add(cat_id)

                for cat_id, delta in stock_deductions.items():
                    if cat_id in cats_por_producto:
                        continue  # handled at product level below
                    stock = await uow.stock_repo.get_by_categoria_id(cat_id)
                    if stock is None:
                        self.logger.warning(
                            "Sin registro de stock para categoria, descuento omitido",
                            categoria_id=cat_id,
                        )
                        continue
                    stock_anterior = stock.cantidad
                    stock.cantidad = max(0, stock.cantidad - delta)
                    stock.fecha_actualizacion = _dt.now()
                    await uow.audit_repo.log_action(
                        username=username or "sistema",
                        entity_type="Stock",
                        entity_id=cat_id,
                        action="UPDATE",
                        changes={
                            "tipo": "VENTA_DESCUENTO",
                            "cantidad_descontada": delta,
                            "stock_anterior": stock_anterior,
                            "stock_nuevo": stock.cantidad,
                            "numero_orden": numero_orden_val,
                        },
                    )

                # Descontar stock por producto para categorías con stock_por_producto=True
                for prod_id, delta in product_stock_deductions.items():
                    prod_stock = await uow.product_stock_repo.get_by_producto_id(prod_id)
                    if prod_stock is None:
                        self.logger.warning(
                            "Sin registro de stock para producto, descuento omitido",
                            producto_id=prod_id,
                        )
                        continue
                    # Only deduct if product belongs to a per-product category
                    cat_id_for_prod = producto_categoria_ids.get(prod_id)
                    if cat_id_for_prod is None or cat_id_for_prod not in cats_por_producto:
                        continue
                    stock_anterior = prod_stock.cantidad
                    prod_stock.cantidad = max(0, prod_stock.cantidad - delta)
                    prod_stock.fecha_actualizacion = _dt.now()
                    await uow.audit_repo.log_action(
                        username=username or "sistema",
                        entity_type="StockProducto",
                        entity_id=prod_id,
                        action="UPDATE",
                        changes={
                            "tipo": "VENTA_DESCUENTO",
                            "cantidad_descontada": delta,
                            "stock_anterior": stock_anterior,
                            "stock_nuevo": prod_stock.cantidad,
                            "numero_orden": numero_orden_val,
                        },
                    )

                await uow.commit()
                await uow.sale_repo.refresh(sale, attribute_names=["items"])

            # Auditar creación (usa su propia transacción)
            if self.audit_service and username:
                await self.audit_service.log_creation(
                    username=username,
                    entity_type="Sale",
                    entity=sale,
                )

            try:
                total_items = 0
                for it in sale.items:
                    if getattr(it, 'oferta_productos_snapshot', None):
                        for p in it.oferta_productos_snapshot:
                            total_items += (p.cantidad or 0) * (it.cantidad or 1)
                    else:
                        total_items += it.cantidad or 0
                setattr(sale, 'total_items', total_items)
            except Exception:
                setattr(sale, 'total_items', 0)

            self.logger.info(
                "Venta creada exitosamente",
                sale_id=sale.id,
                total=float(sale.total),
                items_count=getattr(sale, 'total_items', len(sale.items)),
            )

            return ServiceResult(value=sale, status_code=201)

        except Exception as e:
            self.logger.error(
                "Error al crear venta",
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_by_id(self, sale_id: int) -> ServiceResult:
        """Obtiene una venta por ID."""
        try:
            async with self.uow as uow:
                sale = await uow.sale_repo.get_by_id(sale_id)

            if not sale:
                return ServiceResult(
                    error=f"Venta {sale_id} no encontrada",
                    status_code=404,
                )

            # Compute total_items before returning
            try:
                total_items = 0
                for it in sale.items:
                    if getattr(it, 'oferta_productos_snapshot', None):
                        for p in it.oferta_productos_snapshot:
                            total_items += (p.cantidad or 0) * (it.cantidad or 1)
                    else:
                        total_items += it.cantidad or 0
                setattr(sale, 'total_items', total_items)
            except Exception:
                setattr(sale, 'total_items', 0)

            return ServiceResult(value=sale)

        except Exception as e:
            self.logger.error(
                "Error al obtener venta",
                sale_id=sale_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=500)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> List[Sale]:
        try:
            # Convertir date a datetime
            fecha_desde_dt = datetime.combine(fecha_desde, time.min) if fecha_desde else None
            fecha_hasta_dt = datetime.combine(fecha_hasta, time.max) if fecha_hasta else None
            
            # Loguear parámetros para diagnóstico desde el frontend
            self.logger.debug(
                "Listando ventas - parámetros",
                skip=skip,
                limit=limit,
                fecha_desde=fecha_desde_dt,
                fecha_hasta=fecha_hasta_dt,
            )

            async with self.uow as uow:
                sales = await uow.sale_repo.list(
                    skip=skip,
                    limit=limit,
                    fecha_desde=fecha_desde_dt,
                    fecha_hasta=fecha_hasta_dt,
                )

            # Compute total_items for each sale to provide consistent API responses
            try:
                for sale in sales:
                    total_items = 0
                    for it in sale.items:
                        if getattr(it, 'oferta_productos_snapshot', None):
                            for p in it.oferta_productos_snapshot:
                                total_items += (p.cantidad or 0) * (it.cantidad or 1)
                        else:
                            total_items += it.cantidad or 0
                    setattr(sale, 'total_items', total_items)
            except Exception:
                # If something fails, ensure attribute exists with zero
                for sale in sales:
                    if not hasattr(sale, 'total_items'):
                        setattr(sale, 'total_items', 0)

            # Registrar cantidad obtenida (útil para depuración cuando FE recibe lista vacía)
            try:
                self.logger.debug("Ventas obtenidas", count=len(sales))
            except Exception:
                self.logger.debug("Ventas obtenidas - no se pudo calcular len(sales)")

            return sales
        except Exception as e:
            self.logger.error(
                "Error al listar ventas",
                error=str(e),
                exc_info=True,
            )
            return []

    async def count_all(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> int:
        """Cuenta el total de ventas en la base de datos con filtros opcionales."""
        try:
            # Convertir date a datetime
            fecha_desde_dt = datetime.combine(fecha_desde, time.min) if fecha_desde else None
            fecha_hasta_dt = datetime.combine(fecha_hasta, time.max) if fecha_hasta else None
            
            async with self.uow as uow:
                return await uow.sale_repo.count(
                    fecha_desde=fecha_desde_dt,
                    fecha_hasta=fecha_hasta_dt
                )
        except Exception as e:
            self.logger.error(
                "Error al contar ventas",
                error=str(e),
                exc_info=True,
            )
            return 0

    async def get_available_years(self) -> List[int]:
        """Retorna los años que tienen ventas registradas."""
        try:
            async with self.uow as uow:
                return await uow.sale_repo.get_distinct_years()
        except Exception as e:
            self.logger.error(
                "Error al obtener años disponibles",
                error=str(e),
                exc_info=True,
            )
            return []

    async def update(
        self, 
        sale_id: int, 
        sale_update,
        username: Optional[str] = None,
    ) -> ServiceResult:
        """Actualiza una venta existente.
        
        Nota: El número de orden (numero_orden) no puede ser editado.
        """
        try:
            self.logger.debug(
                "Actualizando venta",
                sale_id=sale_id,
                items_count=len(sale_update.items),
            )

            async with self.uow as uow:
                # Verificar que la venta existe
                existing_sale = await uow.sale_repo.get_by_id(sale_id)
                if not existing_sale:
                    return ServiceResult(
                        error=f"Venta {sale_id} no encontrada",
                        status_code=404,
                    )

                # Capturar estado anterior para auditoría (usando helpers especializados)
                from app.application.utils.audit_helpers import sale_to_snapshot
                old_sale_dict = sale_to_snapshot(existing_sale)

                # Calcular nuevos items y total
                sale_items = []
                total = Decimal("0.00")

                for item in sale_update.items:
                    # Usar precio_unitario recibido, validar que exista
                    if item.precio_unitario is None:
                        return ServiceResult(
                            error="Se debe proporcionar precio_unitario para cada item en la actualización",
                            status_code=400,
                        )
                    
                    precio_unitario = item.precio_unitario
                    item_nombre = None
                    item_descripcion = None
                    item_categoria = None
                    producto_sku = None
                    oferta_productos_snapshot = []
                    
                    # Validar que el producto o oferta existe y cargar snapshot
                    if item.producto_id:
                        producto = await uow.product_repo.get_by_id(item.producto_id)
                        if not producto:
                            return ServiceResult(
                                error=f"Producto {item.producto_id} no encontrado",
                                status_code=404,
                            )
                        
                        # Guardar snapshot del producto
                        item_nombre = producto.nombre
                        producto_sku = producto.sku
                        item_categoria = producto.categoria.nombre if producto.categoria else 'Sin categoría'
                        
                    elif item.oferta_id:
                        oferta = await uow.offer_repo.get_by_id(item.oferta_id)
                        if not oferta:
                            return ServiceResult(
                                error=f"Oferta {item.oferta_id} no encontrada",
                                status_code=404,
                            )
                        
                        # Guardar snapshot de la oferta actual (para referencia)
                        # NOTA: No validamos contra los requisitos actuales de la oferta
                        # porque las ventas son registros históricos que deben preservar
                        # exactamente cómo se hicieron, incluso si la oferta cambió después
                        item_nombre = oferta.nombre
                        item_descripcion = oferta.descripcion
                        item_categoria = 'Ofertas'
                        
                        # Crear snapshot de los productos que el cliente seleccionó
                        # (preservar el snapshot histórico sin validar)
                        if item.productos_seleccionados:
                            for prod_sel in item.productos_seleccionados:
                                # Obtener el producto para hacer el snapshot
                                producto = await uow.product_repo.get_by_id(prod_sel.producto_id)
                                if not producto:
                                    return ServiceResult(
                                        error=f"Producto {prod_sel.producto_id} en productos_seleccionados no encontrado",
                                        status_code=404,
                                    )
                                
                                snapshot = SaleItemOfferProduct(
                                    producto_id=producto.id,
                                    producto_nombre=producto.nombre,
                                    categoria_nombre=producto.categoria.nombre if producto.categoria else 'Sin categoría',
                                    cantidad=prod_sel.cantidad
                                )
                                oferta_productos_snapshot.append(snapshot)
                    
                    elif item.pizza_mitad_mitad:
                        # Para pizzas mitad-mitad en actualizaciones, preservar el snapshot histórico
                        # sin validar contra los requisitos actuales (como con las ofertas)
                        item_nombre = f"Pizza Mitad Mitad"  # Nombre genérico para actualizaciones
                        item_categoria = "Pizza"
                        item_descripcion = None
                    
                    subtotal = Decimal(str(precio_unitario)) * Decimal(str(item.cantidad))
                    total += subtotal
                    
                    sale_item = SaleItem(
                        producto_id=item.producto_id,
                        oferta_id=item.oferta_id,
                        cantidad=item.cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal,
                        # Referencia de negocio (solo productos tienen SKU)
                        producto_sku=producto_sku,
                        # Snapshot completo
                        item_nombre=item_nombre,
                        item_categoria=item_categoria,
                        item_descripcion=item_descripcion,
                        # Identificador de pizza mitad-mitad
                        es_pizza_mitad_mitad=True if item.pizza_mitad_mitad else None,
                        oferta_productos_snapshot=oferta_productos_snapshot
                    )
                    sale_items.append(sale_item)

                # Actualizar venta
                existing_sale.total = total
                existing_sale.fecha_actualizacion = datetime.now()
                existing_sale.items = sale_items

                await uow.sale_repo.update(existing_sale)
                await uow.commit()
                await uow.sale_repo.refresh(existing_sale, attribute_names=["items"])

                # Capturar nuevo estado para comparación
                new_sale_dict = sale_to_snapshot(existing_sale)

            # Auditar actualización con comparación de snapshots
            if self.audit_service and username:
                # Calcular diff manualmente entre snapshots
                diff = {}
                
                # Comparar campos simples
                for key in ['numero_orden', 'total']:
                    old_val = old_sale_dict.get(key)
                    new_val = new_sale_dict.get(key)
                    if old_val != new_val:
                        diff[key] = {"old": old_val, "new": new_val}
                
                # Comparar items
                old_items = old_sale_dict.get('items', [])
                new_items = new_sale_dict.get('items', [])
                if old_items != new_items:
                    diff['items'] = {"old": old_items, "new": new_items}
                
                # Solo registrar si hay cambios
                if diff:
                    async with self.uow as uow:
                        await uow.audit_repo.log_action(
                            username=username,
                            entity_type="Sale",
                            entity_id=existing_sale.id,
                            action="UPDATE",
                            changes=diff,
                        )
                        await uow.commit()

            self.logger.info(
                "Venta actualizada exitosamente",
                sale_id=sale_id,
                total=float(existing_sale.total),
                items_count=len(existing_sale.items),
            )

            return ServiceResult(value=existing_sale)

        except Exception as e:
            self.logger.error(
                "Error al actualizar venta",
                sale_id=sale_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def delete(
        self, 
        sale_id: int,
        username: Optional[str] = None
    ) -> ServiceResult:
        """Elimina una venta."""
        try:
            self.logger.debug("Eliminando venta", sale_id=sale_id)

            async with self.uow as uow:
                sale = await uow.sale_repo.get_by_id(sale_id)
                
                if not sale:
                    return ServiceResult(
                        error=f"Venta {sale_id} no encontrada",
                        status_code=404,
                    )

                # Auditar eliminación ANTES de borrar (AuditService usa su propia transacción)
                if self.audit_service and username:
                    await self.audit_service.log_deletion(
                        username=username,
                        entity_type="Sale",
                        entity=sale,
                    )

                await uow.sale_repo.delete(sale_id)
                await uow.commit()

            self.logger.info("Venta eliminada exitosamente", sale_id=sale_id)

            return ServiceResult(status_code=204)

        except Exception as e:
            self.logger.error(
                "Error al eliminar venta",
                sale_id=sale_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    def _get_pizza_mitad_mitad_price(self, producto_izq, producto_der) -> Optional[Decimal]:
        """Calcula el precio para pizza mitad-mitad (precio de la pizza más cara)."""
        precio_izq = self._get_product_price(producto_izq, 1)
        precio_der = self._get_product_price(producto_der, 1)
        
        if precio_izq is None or precio_der is None:
            return None
        
        return max(precio_izq, precio_der)  # Precio de la pizza más cara

    async def _validate_pizza_mitad_mitad(self, pizza_mitad_mitad, uow) -> Optional[ServiceResult]:
        """Valida que la configuración de pizza mitad-mitad sea correcta."""
        # Validar que ambos productos existan
        producto_izq = await uow.product_repo.get_by_id(pizza_mitad_mitad.producto_id_izquierda)
        producto_der = await uow.product_repo.get_by_id(pizza_mitad_mitad.producto_id_derecha)
        
        if not producto_izq:
            return ServiceResult(
                error=f"Producto {pizza_mitad_mitad.producto_id_izquierda} no encontrado",
                status_code=404,
            )
        
        if not producto_der:
            return ServiceResult(
                error=f"Producto {pizza_mitad_mitad.producto_id_derecha} no encontrado",
                status_code=404,
            )
        
        # Validar que ambos productos estén activos
        if not producto_izq.activo or not producto_der.activo:
            return ServiceResult(
                error="Ambos productos deben estar activos",
                status_code=400,
            )
        
        # Validar que ambos sean pizzas
        if not self._es_pizza(producto_izq) or not self._es_pizza(producto_der):
            return ServiceResult(
                error="Ambos productos deben ser pizzas",
                status_code=400,
            )
        
        # Validar que sean sabores diferentes (ya se valida en el schema, pero por si acaso)
        if producto_izq.id == producto_der.id:
            return ServiceResult(
                error="Los sabores deben ser diferentes",
                status_code=400,
            )
        
        return None

    def _es_pizza(self, producto) -> bool:
        """Verifica si un producto es una pizza."""
        # Opción 1: Por categoría (si existe categoría "Pizzas")
        if producto.categoria and producto.categoria.nombre.lower() == "pizzas":
            return True
        
        # Opción 2: Por nombre (contiene "pizza")
        if "pizza" in producto.nombre.lower():
            return True
        
        # Opción 3: Por ID de categoría (ajustar según tu base de datos)
        # Aquí podrías agregar IDs específicos de categorías de pizzas
        
        return False
