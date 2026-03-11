"""
DB integration benchmarks conftest.

Reads BENCH_DB_* variables from backend/.env.benchmark.
Drops + recreates all tables, seeds realistic data, tears down at end of session.

REQUIRED: The benchmark database must exist before running:
    psql -U postgres -c "CREATE DATABASE PizzaFiori_benchmark;"

Run:
    .venv\\Scripts\\pytest tests/benchmarks/repositories --no-cov --benchmark-autosave --benchmark-storage=benchmark_results/
"""

import asyncio
import os
from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import pytest
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# ── Load .env.benchmark BEFORE any settings-dependent import ─────────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
_BENCH_ENV = _BACKEND_DIR / ".env.benchmark"

if not _BENCH_ENV.exists():
    pytest.skip(
        f".env.benchmark not found at {_BENCH_ENV}. "
        "Create it with BENCH_DB_* variables to run DB benchmarks.",
        allow_module_level=True,
    )

load_dotenv(dotenv_path=str(_BENCH_ENV), override=True)

# ── Build benchmark-specific engine (isolated from production DB) ─────────────
_DB_URL = (
    f"postgresql+asyncpg://"
    f"{quote(os.environ['BENCH_DB_USER'])}:{quote(os.environ['BENCH_DB_PASSWORD'])}"
    f"@{os.environ['BENCH_DB_HOST']}:{os.environ['BENCH_DB_PORT']}"
    f"/{os.environ['BENCH_DB_NAME']}"
)

# Import domain models AFTER env load so settings loads from .env correctly
from app.domain.models.base import Base
import app.domain.models  # noqa: F401 — registers all SQLAlchemy models with Base.metadata

from app.domain.models.product_category import ProductCategory
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.models.offer import Offer
from app.domain.models.offer_item import OfferItem, oferta_item_productos
from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.models.expense_category import ExpenseCategory
from app.domain.models.expense import Expense
from app.domain.models.user import User
from app.domain.models.category_stock import CategoryStock
from app.domain.models.audit_log import AuditLog
from app.domain.models.order_daily_sequence import OrderDailySequence
from app.application.user_service import hash_password

_engine = create_async_engine(
    _DB_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
)
_SessionFactory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Populated by _seed() — safe to read from fixtures after bench_db_lifecycle
_SEEDED_IDS: dict = {
    "cat_pizzas_id": 0,
    "cat_empanadas_id": 0,
    "product_ids": [],
    "offer_id": 0,
    "expense_cat_root_id": 0,
    "expense_cat_sub_id": 0,
    "first_sale_id": 0,
    "first_product_id": 0,
    "first_expense_id": 0,
    "admin_user_id": 0,
    "regular_user_id": 0,
    "admin_username": "bench_admin",
    "first_audit_id": 0,
    "first_audit_entity_id": 0,
    "first_sequence_date": None,
}


# ── Schema management ─────────────────────────────────────────────────────────

async def _create_schema() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def _drop_schema() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Seed ──────────────────────────────────────────────────────────────────────

async def _seed() -> None:
    async with _SessionFactory() as session:
        # Product categories
        cat_pizzas = ProductCategory(nombre="Pizzas", activo=True)
        cat_empanadas = ProductCategory(nombre="Empanadas", activo=True)
        session.add_all([cat_pizzas, cat_empanadas])
        await session.flush()
        _SEEDED_IDS["cat_pizzas_id"] = cat_pizzas.id
        _SEEDED_IDS["cat_empanadas_id"] = cat_empanadas.id

        # Products: 10 total (5 per category), 2 price tiers each
        products: list[tuple[Product, str]] = []
        for i in range(1, 11):
            cat = cat_pizzas if i <= 5 else cat_empanadas
            cat_name = "Pizzas" if i <= 5 else "Empanadas"
            p = Product(
                sku=f"BENCH-{i:03d}",
                nombre=f"Producto Benchmark {i}",
                categoria_id=cat.id,
                activo=True,
            )
            session.add(p)
            await session.flush()
            session.add(ProductPrice(
                producto_id=p.id,
                cantidad=1,
                precio=Decimal(f"{800 + i * 100}.00"),
            ))
            session.add(ProductPrice(
                producto_id=p.id,
                cantidad=2,
                precio=Decimal(f"{1400 + i * 150}.00"),
            ))
            products.append((p, cat_name))

        await session.flush()
        _SEEDED_IDS["product_ids"] = [p.id for p, _ in products]
        _SEEDED_IDS["first_product_id"] = products[0][0].id

        # Offer with 2 items (one item per category type)
        oferta = Offer(
            nombre="Combo Benchmark",
            descripcion="Oferta de prueba para benchmarks",
            precio=Decimal("2500.00"),
            activo=True,
        )
        session.add(oferta)
        await session.flush()
        _SEEDED_IDS["offer_id"] = oferta.id

        item1 = OfferItem(oferta_id=oferta.id, categoria_id=cat_pizzas.id, cantidad=1)
        item2 = OfferItem(oferta_id=oferta.id, categoria_id=cat_empanadas.id, cantidad=2)
        session.add_all([item1, item2])
        await session.flush()
        await session.execute(
            oferta_item_productos.insert().values([
                {"oferta_item_id": item1.id, "producto_id": products[0][0].id},
                {"oferta_item_id": item2.id, "producto_id": products[5][0].id},
            ])
        )

        # Expense categories: 2 roots + 2 subcategories
        cat_op = ExpenseCategory(nombre="Operacional", activo=True)
        cat_personal = ExpenseCategory(nombre="Personal", activo=True)
        session.add_all([cat_op, cat_personal])
        await session.flush()
        _SEEDED_IDS["expense_cat_root_id"] = cat_op.id

        cat_materia = ExpenseCategory(nombre="Materia Prima", padre_id=cat_op.id, activo=True)
        cat_sueldos = ExpenseCategory(nombre="Sueldos", padre_id=cat_personal.id, activo=True)
        session.add_all([cat_materia, cat_sueldos])
        await session.flush()
        _SEEDED_IDS["expense_cat_sub_id"] = cat_materia.id

        # Expenses: 30 records spread over last 60 days
        base_date = date.today()
        first_expense_id = None
        for i in range(30):
            e = Expense(
                categoria_gasto_id=cat_materia.id if i % 2 == 0 else cat_sueldos.id,
                descripcion=f"Gasto benchmark {i + 1}",
                monto=Decimal(f"{500 + i * 50}.00"),
                fecha_pago=base_date - timedelta(days=i * 2),
                activo=True,
            )
            session.add(e)
            await session.flush()
            if first_expense_id is None:
                first_expense_id = e.id
        _SEEDED_IDS["first_expense_id"] = first_expense_id

        # Sales: 50 records spread over last 58 days, 2 items each
        base_dt = datetime.now()
        first_sale_id = None
        for i in range(50):
            venta_dt = base_dt - timedelta(hours=i * 28)
            sale = Sale(
                numero_orden=f"ORD-BENCH-{i + 1:04d}",
                total=Decimal(f"{1000 + i * 50}.00"),
                fecha_creacion=venta_dt,
            )
            session.add(sale)
            await session.flush()
            if first_sale_id is None:
                first_sale_id = sale.id

            p, cat_name = products[i % 10]
            p2, cat_name2 = products[(i + 1) % 10]
            session.add(SaleItem(
                venta_id=sale.id,
                producto_id=p.id,
                cantidad=1,
                precio_unitario=Decimal(f"{800 + (i % 10) * 100}.00"),
                subtotal=Decimal(f"{800 + (i % 10) * 100}.00"),
                producto_sku=p.sku,
                item_nombre=p.nombre,
                item_categoria=cat_name,
                es_pizza_mitad_mitad=False,
            ))
            session.add(SaleItem(
                venta_id=sale.id,
                producto_id=p2.id,
                cantidad=2,
                precio_unitario=Decimal(f"{800 + ((i + 1) % 10) * 100}.00"),
                subtotal=Decimal(f"{1600 + ((i + 1) % 10) * 200}.00"),
                producto_sku=p2.sku,
                item_nombre=p2.nombre,
                item_categoria=cat_name2,
                es_pizza_mitad_mitad=False,
            ))
        _SEEDED_IDS["first_sale_id"] = first_sale_id

        # Users: 1 admin + 5 regular users
        admin = User(
            username="bench_admin",
            email="bench_admin@benchmark.test",
            password_hash=hash_password("BenchPass123!"),
            first_name="Bench",
            last_name="Admin",
            role="ADMIN",
        )
        session.add(admin)
        await session.flush()
        _SEEDED_IDS["admin_user_id"] = admin.id

        for i in range(1, 6):
            u = User(
                username=f"bench_user_{i}",
                email=f"bench_user_{i}@benchmark.test",
                password_hash=hash_password("BenchPass123!"),
                first_name=f"User{i}",
                last_name="Bench",
                role="USER",
            )
            session.add(u)
            await session.flush()
            if i == 1:
                _SEEDED_IDS["regular_user_id"] = u.id

        # CategoryStock: one stock record per product category
        for cat, qty, amarillo, rojo in [
            (cat_pizzas, 50, 20, 10),
            (cat_empanadas, 30, 15, 5),
        ]:
            session.add(CategoryStock(
                categoria_id=cat.id,
                cantidad=qty,
                umbral_amarillo=amarillo,
                umbral_rojo=rojo,
            ))
        await session.flush()

        # AuditLog: 40 records — mix of entities, actions, users
        base_audit_dt = datetime.now()
        first_audit_id = None
        first_audit_entity_id = None
        entity_types = ["Product", "Sale", "Expense", "User", "Offer"]
        actions = ["CREATE", "UPDATE", "DELETE"]
        for i in range(40):
            entity_type = entity_types[i % len(entity_types)]
            action = actions[i % len(actions)]
            al = AuditLog(
                username="bench_admin" if i % 3 == 0 else f"bench_user_{(i % 5) + 1}",
                entity_type=entity_type,
                entity_id=i + 1,
                action=action,
                changes={"old": {"campo": f"valor_viejo_{i}"}, "new": {"campo": f"valor_nuevo_{i}"}},
                timestamp=base_audit_dt - timedelta(hours=i * 6),
            )
            session.add(al)
            await session.flush()
            if first_audit_id is None:
                first_audit_id = al.id
                first_audit_entity_id = al.entity_id
        _SEEDED_IDS["first_audit_id"] = first_audit_id
        _SEEDED_IDS["first_audit_entity_id"] = first_audit_entity_id

        # OrderDailySequence: 7 records (one per day for last week)
        today = date.today()
        for delta in range(7):
            d = today - timedelta(days=delta)
            session.add(OrderDailySequence(business_date=d, last_value=10 + delta))
        await session.flush()
        _SEEDED_IDS["first_sequence_date"] = today

        await session.commit()


# ── Session-scoped lifecycle (autouse — runs once per pytest session) ─────────

@pytest.fixture(scope="session", autouse=True)
def bench_db_lifecycle():
    """Drop + recreate schema, seed data. Drop tables at end of session.

    Uses two separate event loops (setup and teardown) to avoid asyncpg
    "Future attached to a different loop" errors: pool connections created
    during seeding are disposed before the benchmark modules start their own
    event loops.
    """
    # ── Setup (dedicated loop, disposed before yield) ─────────────────────
    loop_setup = asyncio.new_event_loop()
    try:
        loop_setup.run_until_complete(_create_schema())
        loop_setup.run_until_complete(_seed())
        # CRITICAL: dispose all pool connections so benchmark modules can
        # create fresh connections on their own event loops.
        loop_setup.run_until_complete(_engine.dispose())
    finally:
        loop_setup.close()

    yield  # benchmark modules run here with isolated per-module event loops

    # ── Teardown (fresh loop) ──────────────────────────────────────────────
    loop_teardown = asyncio.new_event_loop()
    try:
        loop_teardown.run_until_complete(_drop_schema())
        loop_teardown.run_until_complete(_engine.dispose())
    finally:
        loop_teardown.close()


@pytest.fixture(scope="session")
def seeded_ids(bench_db_lifecycle):
    """Exposes seeded primary-key IDs to all benchmark modules."""
    return _SEEDED_IDS


# ── Module-scoped helpers (same pattern as application benchmarks) ─────────────

@pytest.fixture(scope="module")
def event_loop():
    """Module-scoped event loop — reused across every benchmark in the module.

    Disposes the engine pool BEFORE closing so benchmark connections are
    released cleanly. This prevents lifecycle teardown from getting connections
    that belong to a closed event loop.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(_engine.dispose())
    loop.close()


@pytest.fixture(scope="module")
def run_async(event_loop):
    """Runs an async callable synchronously using the module event loop."""
    def _run(async_fn, *args, **kwargs):
        return event_loop.run_until_complete(async_fn(*args, **kwargs))
    return _run


@pytest.fixture(scope="module")
def session_factory(bench_db_lifecycle):
    """Exposes the async_sessionmaker so benchmarks create isolated per-call sessions."""
    return _SessionFactory
