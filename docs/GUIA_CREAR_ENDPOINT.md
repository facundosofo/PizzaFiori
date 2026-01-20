# Guía para Crear un Endpoint en PizzaFiori

Esta guía describe paso a paso cómo crear un nuevo endpoint siguiendo la arquitectura Clean Architecture implementada en el proyecto, respetando todos los patrones de diseño utilizados.

## Patrones Implementados

- **Clean Architecture**: Separación en capas (Domain, Application, Infrastructure, Presentation)
- **Repository Pattern**: Abstracción del acceso a datos
- **Unit of Work**: Gestión transaccional de operaciones
- **Dependency Injection**: Usando `dependency-injector`
- **Service Layer**: Lógica de negocio centralizada

---

## Arquitectura por Capas

```
Domain Layer (Reglas de Negocio)
├── models/          # Entidades SQLAlchemy
└── repositories/    # Interfaces abstractas de repositorios

Application Layer (Casos de Uso)
└── [feature]_service.py  # Lógica de negocio

Infrastructure Layer (Implementaciones)
├── repositories/    # Implementaciones concretas de repositorios
├── database.py      # Configuración de BD
└── unit_of_work.py  # Implementación del UoW

Presentation Layer (API)
├── routers/         # Endpoints FastAPI
└── schemas/         # Modelos Pydantic
```

---

## Ejemplo: Crear el Módulo "Orders" (Pedidos)

Vamos a crear un módulo completo para gestionar pedidos como ejemplo.

---

## PASO 1: Crear el Modelo de Dominio

**Archivo:** `backend/app/domain/models/order.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum
from sqlalchemy.orm import relationship
import enum

from app.domain.models.base import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "Pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente_nombre = Column(String(255), nullable=False)
    cliente_telefono = Column(String(50), nullable=False)
    direccion_entrega = Column(String(500), nullable=True)
    total = Column(Numeric(10, 2), nullable=False)
    estado = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    notas = Column(String(1000), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    items = relationship(
        "OrderItem",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, cliente={self.cliente_nombre}, estado={self.estado})>"
```

**Archivo:** `backend/app/domain/models/order_item.py`

```python
from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.domain.models.base import Base


class OrderItem(Base):
    __tablename__ = "PedidoItems"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("Pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("Productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    # Relaciones
    pedido = relationship("Order", back_populates="items")
    producto = relationship("Product")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, producto_id={self.producto_id}, cantidad={self.cantidad})>"
```

---

## PASO 2: Crear el Repositorio Abstracto (Domain)

**Archivo:** `backend/app/domain/repositories/order_repository.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.order import Order, OrderStatus


class AbstractOrderRepository(ABC):
    """
    Repositorio abstracto para Order.
    Define el contrato que deben cumplir las implementaciones concretas.
    """

    @abstractmethod
    async def add(self, order: Order) -> Order:
        """Agrega un nuevo pedido a la base de datos."""
        ...

    @abstractmethod
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Obtiene un pedido por su ID, incluyendo sus items."""
        ...

    @abstractmethod
    async def list(
        self,
        estado: Optional[OrderStatus] = None,
        cliente_nombre: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Lista pedidos con filtros opcionales."""
        ...

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """Actualiza un pedido existente."""
        ...

    @abstractmethod
    async def delete(self, order_id: int) -> bool:
        """Elimina un pedido por su ID."""
        ...

    @abstractmethod
    async def refresh(
        self,
        order: Order,
        attribute_names: Optional[list] = None,
    ) -> None:
        """Refresca una instancia desde la BD."""
        ...
```

---

## PASO 3: Crear el Repositorio Concreto (Infrastructure)

**Archivo:** `backend/app/infrastructure/repositories/order_repository.py`

```python
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.order import Order, OrderStatus
from app.domain.repositories.order_repository import AbstractOrderRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyOrderRepository(BaseRepository[Order], AbstractOrderRepository):
    """
    Implementación concreta del repositorio de pedidos usando SQLAlchemy.
    """
    model = Order

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Obtiene un pedido por ID con sus items relacionados."""
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(
        self,
        estado: Optional[OrderStatus] = None,
        cliente_nombre: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Lista pedidos con filtros y paginación."""
        query = select(Order).options(selectinload(Order.items))

        conditions = []
        if estado is not None:
            conditions.append(Order.estado == estado)
        if cliente_nombre is not None:
            conditions.append(Order.cliente_nombre.ilike(f"%{cliente_nombre}%"))

        if conditions:
            query = query.where(*conditions)

        query = query.offset(skip).limit(limit).order_by(Order.fecha_creacion.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, order: Order) -> Order:
        """Actualiza un pedido."""
        await self.session.merge(order)
        return order

    async def delete(self, order_id: int) -> bool:
        """Elimina un pedido."""
        stmt = delete(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
```

---

## PASO 4: Agregar el Repositorio al Unit of Work

### 4.1 Actualizar la interfaz abstracta

**Archivo:** `backend/app/domain/unit_of_work.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.repositories.category_repository import AbstractCategoryRepository
from app.domain.repositories.product_repository import AbstractProductRepository
from app.domain.repositories.order_repository import AbstractOrderRepository  # ✅ NUEVO


class AbstractUnitOfWork(ABC):
    product_repo: AbstractProductRepository
    category_repo: AbstractCategoryRepository
    order_repo: AbstractOrderRepository  # ✅ NUEVO

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...
```

### 4.2 Actualizar la implementación concreta

**Archivo:** `backend/app/infrastructure/unit_of_work.py`

```python
from __future__ import annotations

from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.repositories.category_repository import SqlAlchemyCategoryRepository
from app.infrastructure.repositories.product_repository import SqlAlchemyProductRepository
from app.infrastructure.repositories.order_repository import SqlAlchemyOrderRepository  # ✅ NUEVO


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=AsyncSessionLocal):
        self.session_factory = session_factory
        self.session = None
        self.product_repo = None
        self.category_repo = None
        self.order_repo = None  # ✅ NUEVO

    async def __aenter__(self):
        self.session = self.session_factory()
        self.product_repo = SqlAlchemyProductRepository(self.session)
        self.category_repo = SqlAlchemyCategoryRepository(self.session)
        self.order_repo = SqlAlchemyOrderRepository(self.session)  # ✅ NUEVO
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        if self.session:
            await self.session.rollback()
```

---

## PASO 5: Crear los Schemas de Pydantic (Presentation)

**Archivo:** `backend/app/presentation/schemas/order_schemas.py`

```python
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import List, Optional

from app.domain.models.order import OrderStatus


# ======================================================
# Order Items
# ======================================================

class OrderItemRequest(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, le=100)
    precio_unitario: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)


class OrderItemResponse(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


# ======================================================
# Request Models
# ======================================================

class OrderCreateRequest(BaseModel):
    cliente_nombre: str = Field(..., min_length=1, max_length=255)
    cliente_telefono: str = Field(..., min_length=7, max_length=50)
    direccion_entrega: Optional[str] = Field(None, max_length=500)
    notas: Optional[str] = Field(None, max_length=1000)
    items: List[OrderItemRequest] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_items(self):
        if not self.items or len(self.items) == 0:
            raise ValueError("El pedido debe tener al menos un item")
        return self


class OrderUpdateRequest(BaseModel):
    estado: Optional[OrderStatus] = None
    direccion_entrega: Optional[str] = Field(None, max_length=500)
    notas: Optional[str] = Field(None, max_length=1000)


# ======================================================
# Response Models
# ======================================================

class OrderResponse(BaseModel):
    id: int
    cliente_nombre: str
    cliente_telefono: str
    direccion_entrega: Optional[str]
    total: Decimal
    estado: OrderStatus
    notas: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)
```

---

## PASO 6: Crear el Service (Application)

**Archivo:** `backend/app/application/order_service.py`

```python
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import structlog

from app.domain.models.order import Order, OrderStatus
from app.domain.models.order_item import OrderItem
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.order_schemas import (
    OrderCreateRequest,
    OrderUpdateRequest,
)


@dataclass
class ServiceResult:
    """Resultado de una operación de servicio."""
    value: Optional[Order | List[Order]] = None
    error: Optional[str] = None
    status_code: int = 200


class OrderService:
    """
    Servicio de aplicación para gestionar pedidos.
    Contiene la lógica de negocio y coordina las operaciones.
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)

    async def create(
        self, order_create: OrderCreateRequest
    ) -> ServiceResult:
        """Crea un nuevo pedido."""
        try:
            self.logger.debug(
                "Creando pedido",
                cliente=order_create.cliente_nombre,
                items_count=len(order_create.items),
            )

            # Calcular el total
            total = sum(
                item.cantidad * item.precio_unitario
                for item in order_create.items
            )

            async with self.uow as uow:
                # Crear el pedido
                order = Order(
                    cliente_nombre=order_create.cliente_nombre,
                    cliente_telefono=order_create.cliente_telefono,
                    direccion_entrega=order_create.direccion_entrega,
                    total=total,
                    estado=OrderStatus.PENDING,
                    notas=order_create.notas,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                    items=[
                        OrderItem(
                            producto_id=item.producto_id,
                            cantidad=item.cantidad,
                            precio_unitario=item.precio_unitario,
                            subtotal=item.cantidad * item.precio_unitario,
                        )
                        for item in order_create.items
                    ],
                )

                await uow.order_repo.add(order)
                await uow.commit()
                await uow.order_repo.refresh(order, attribute_names=["items"])

            self.logger.info(
                "Pedido creado exitosamente",
                order_id=order.id,
                total=float(order.total),
            )

            return ServiceResult(value=order, status_code=201)

        except Exception as e:
            self.logger.error(
                "Error al crear pedido",
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_by_id(self, order_id: int) -> ServiceResult:
        """Obtiene un pedido por ID."""
        try:
            async with self.uow as uow:
                order = await uow.order_repo.get_by_id(order_id)

            if not order:
                return ServiceResult(
                    error=f"Pedido {order_id} no encontrado",
                    status_code=404,
                )

            return ServiceResult(value=order)

        except Exception as e:
            self.logger.error(
                "Error al obtener pedido",
                order_id=order_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=500)

    async def get_all(
        self,
        estado: Optional[OrderStatus] = None,
        cliente_nombre: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Lista todos los pedidos con filtros opcionales."""
        async with self.uow as uow:
            return await uow.order_repo.list(
                estado=estado,
                cliente_nombre=cliente_nombre,
                skip=skip,
                limit=limit,
            )

    async def update(
        self, order_id: int, order_update: OrderUpdateRequest
    ) -> ServiceResult:
        """Actualiza un pedido."""
        try:
            async with self.uow as uow:
                order = await uow.order_repo.get_by_id(order_id)

                if not order:
                    return ServiceResult(
                        error=f"Pedido {order_id} no encontrado",
                        status_code=404,
                    )

                # Actualizar campos si se proporcionan
                if order_update.estado is not None:
                    order.estado = order_update.estado
                if order_update.direccion_entrega is not None:
                    order.direccion_entrega = order_update.direccion_entrega
                if order_update.notas is not None:
                    order.notas = order_update.notas

                order.fecha_actualizacion = datetime.now()

                await uow.order_repo.update(order)
                await uow.commit()
                await uow.order_repo.refresh(order, attribute_names=["items"])

            self.logger.info("Pedido actualizado", order_id=order_id)

            return ServiceResult(value=order)

        except Exception as e:
            self.logger.error(
                "Error al actualizar pedido",
                order_id=order_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def delete(self, order_id: int) -> ServiceResult:
        """Elimina un pedido."""
        try:
            async with self.uow as uow:
                order = await uow.order_repo.get_by_id(order_id)

                if not order:
                    return ServiceResult(
                        error=f"Pedido {order_id} no encontrado",
                        status_code=404,
                    )

                await uow.order_repo.delete(order_id)
                await uow.commit()

            self.logger.info("Pedido eliminado", order_id=order_id)

            return ServiceResult(status_code=204)

        except Exception as e:
            self.logger.error(
                "Error al eliminar pedido",
                order_id=order_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)
```

---

## PASO 7: Crear el Router (Presentation)

**Archivo:** `backend/app/presentation/routers/order_router.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from dependency_injector.wiring import inject, Provide
from typing import List, Optional

from app.application.order_service import OrderService, ServiceResult
from app.containers import Container
from app.presentation.schemas.order_schemas import (
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderResponse,
)
from app.domain.models.order import OrderStatus


router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un pedido",
    description="Crea un nuevo pedido con sus items.",
)
@inject
async def create_order(
    order: OrderCreateRequest,
    service: OrderService = Depends(Provide[Container.order_service]),
):
    result: ServiceResult = await service.create(order)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="Obtener todos los pedidos",
    description="Devuelve la lista de pedidos con filtros opcionales.",
)
@inject
async def get_orders(
    estado: Optional[OrderStatus] = Query(None, description="Filtrar por estado"),
    cliente: Optional[str] = Query(None, description="Buscar por nombre de cliente"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros"),
    service: OrderService = Depends(Provide[Container.order_service]),
):
    return await service.get_all(
        estado=estado,
        cliente_nombre=cliente,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Obtener un pedido por ID",
    description="Devuelve un pedido específico por su ID.",
    responses={404: {"description": "Pedido no encontrado"}},
)
@inject
async def get_order(
    order_id: int = Path(..., ge=1, description="ID único del pedido"),
    service: OrderService = Depends(Provide[Container.order_service]),
):
    result: ServiceResult = await service.get_by_id(order_id)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Actualizar un pedido",
    description="Actualiza el estado o información de un pedido.",
    responses={404: {"description": "Pedido no encontrado"}},
)
@inject
async def update_order(
    order_id: int,
    order_update: OrderUpdateRequest,
    service: OrderService = Depends(Provide[Container.order_service]),
):
    result: ServiceResult = await service.update(order_id, order_update)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un pedido",
    description="Elimina un pedido por su ID.",
    responses={404: {"description": "Pedido no encontrado"}},
)
@inject
async def delete_order(
    order_id: int = Path(..., ge=1, description="ID único del pedido"),
    service: OrderService = Depends(Provide[Container.order_service]),
):
    result: ServiceResult = await service.delete(order_id)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return None
```

---

## PASO 8: Configurar Dependency Injection

**Archivo:** `backend/app/containers.py`

```python
from dependency_injector import containers, providers

from app.application.category_service import CategoryService
from app.application.product_service import ProductService
from app.application.order_service import OrderService  # ✅ NUEVO
from app.infrastructure.file_service import FileService
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.logging import configure_logging


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.presentation.routers.product_router",
            "app.presentation.routers.category_router",
            "app.presentation.routers.order_router",  # ✅ NUEVO
        ]
    )
    
    logging = providers.Singleton(configure_logging)
    
    file_service = providers.Singleton(FileService)
    unit_of_work = providers.Factory(SqlAlchemyUnitOfWork)

    product_service = providers.Factory(
        ProductService,
        uow=unit_of_work,
        file_service=file_service,
        logger=logging,
    )

    category_service = providers.Factory(
        CategoryService,
        uow=unit_of_work,
        logger=logging,
    )

    # ✅ NUEVO
    order_service = providers.Factory(
        OrderService,
        uow=unit_of_work,
        logger=logging,
    )
```

---

## PASO 9: Registrar el Router en la Aplicación

**Archivo:** `backend/app/main.py`

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .presentation.routers.product_router import router as product_router
from .presentation.routers.category_router import router as category_router
from .presentation.routers.order_router import router as order_router  # ✅ NUEVO
from app.domain import *
from app.containers import Container
from app.infrastructure.middleware.http_logging_middleware import HttpLoggingMiddleware
from app.infrastructure.config.settings import settings
from app.infrastructure.logging import get_logger

container = Container()
container.wire()

logger = container.logging()
logger.debug("Inicializando PizzaFiori API")

app = FastAPI(title="PizzaFiori API")

app.add_middleware(
    HttpLoggingMiddleware,
    logger=get_logger("http.external"),
    log_response_body=settings.debug,
    max_body_size=50_000,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Registrar routers
app.include_router(product_router)
app.include_router(category_router)
app.include_router(order_router)  # ✅ NUEVO

@app.get("/")
def root():
    return {"mensaje": "API PizzaFiori funcionando"}
```

---

## PASO 10: Crear la Migración de Alembic

```bash
cd backend
alembic revision --autogenerate -m "add orders tables"
```

Revisa el archivo de migración generado en `backend/alembic/versions/` y luego aplícalo:

```bash
alembic upgrade head
```

---

## Checklist de Creación de Endpoint

- [ ] **Paso 1**: Crear modelo(s) de dominio en `domain/models/`
- [ ] **Paso 2**: Crear repositorio abstracto en `domain/repositories/`
- [ ] **Paso 3**: Crear repositorio concreto en `infrastructure/repositories/`
- [ ] **Paso 4**: Agregar repositorio al Unit of Work (abstracto e implementación)
- [ ] **Paso 5**: Crear schemas Pydantic en `presentation/schemas/`
- [ ] **Paso 6**: Crear service en `application/`
- [ ] **Paso 7**: Crear router en `presentation/routers/`
- [ ] **Paso 8**: Configurar DI en `containers.py`
- [ ] **Paso 9**: Registrar router en `main.py`
- [ ] **Paso 10**: Crear y aplicar migración con Alembic
- [ ] **Paso 11**: Probar endpoints con herramientas como Postman o Swagger UI

---

## Convenciones y Mejores Prácticas

### Nomenclatura

- **Modelos**: Singular en inglés (`Order`, `Product`, `Category`)
- **Tablas**: Plural en español (`Pedidos`, `Productos`, `Categorias`)
- **Servicios**: `[Entity]Service` (`OrderService`)
- **Repositorios**: `Abstract[Entity]Repository` y `SqlAlchemy[Entity]Repository`
- **Schemas**: `[Entity][Action]Request/Response` (`OrderCreateRequest`)

### Organización del Código

- **Domain**: No debe tener dependencias externas (solo abstracciones)
- **Application**: Coordina casos de uso, no accede directamente a BD
- **Infrastructure**: Implementaciones concretas, acceso a BD
- **Presentation**: Validación de entrada, serialización de salida

### Gestión de Errores

```python
@dataclass
class ServiceResult:
    value: Optional[Any] = None
    error: Optional[str] = None
    status_code: int = 200
```

Siempre retornar `ServiceResult` desde los servicios y manejar errores en el router.

### Logging

Usar structured logging con `structlog`:

```python
self.logger.debug("Operación iniciada", entity_id=123, action="create")
self.logger.error("Error en operación", error=str(e), exc_info=True)
```

### Transacciones

Siempre usar el Unit of Work para operaciones que modifican datos:

```python
async with self.uow as uow:
    entity = await uow.entity_repo.add(entity)
    await uow.commit()  # Commit explícito
    await uow.entity_repo.refresh(entity)  # Refrescar relaciones
```

### Validaciones

- Validaciones de formato/estructura: Pydantic schemas
- Validaciones de negocio: Service layer
- Validaciones de BD: Constraints de SQLAlchemy

---

## Recursos Adicionales

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Dependency Injector](https://python-dependency-injector.ets-labs.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## Notas Finales

Esta estructura proporciona:

✅ **Separación de responsabilidades** clara entre capas  
✅ **Testabilidad** alta gracias a las abstracciones  
✅ **Mantenibilidad** mediante patrones consistentes  
✅ **Escalabilidad** para nuevos módulos  
✅ **Dependency Injection** automatizada  

Cada nueva funcionalidad debe seguir estos mismos pasos para mantener la consistencia arquitectónica del proyecto.
