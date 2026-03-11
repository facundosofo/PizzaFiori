"""
Repository-layer DB benchmarks: products and product categories.

Each benchmark iteration creates a fresh AsyncSession from the pool, executes
a real PostgreSQL query, then closes the session. This models the per-request
session lifecycle used in production (FastAPI dependency injection).

Data seeded: 2 categories, 10 products (5 per category), 2 price tiers each.
"""

from app.infrastructure.repositories.product_category_repository import (
    SqlAlchemyProductCategoryRepository,
)
from app.infrastructure.repositories.product_repository import SqlAlchemyProductRepository


# ── ProductCategory ───────────────────────────────────────────────────────────

def bench_db_product_category_list_all(benchmark, run_async, session_factory):
    """SELECT all product categories (no filter)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductCategoryRepository(session).list()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_category_list_active(benchmark, run_async, session_factory):
    """SELECT active product categories only."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductCategoryRepository(session).list_by_active(activo=True)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_category_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single category by PK."""
    cid = seeded_ids["cat_pizzas_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductCategoryRepository(session).get_by_id(cid)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


# ── Product ───────────────────────────────────────────────────────────────────

def bench_db_product_list_all(benchmark, run_async, session_factory):
    """SELECT all products with prices + category (selectinload)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductRepository(session).list()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_list_active(benchmark, run_async, session_factory):
    """SELECT active products only (WHERE activo = true)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductRepository(session).list(active=True)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_list_by_category(benchmark, run_async, session_factory, seeded_ids):
    """SELECT products filtered by category (5 results)."""
    cat_id = seeded_ids["cat_pizzas_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductRepository(session).list(categoria_id=cat_id)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single product by PK with prices + category loaded."""
    pid = seeded_ids["first_product_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductRepository(session).get_by_id(pid)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_get_by_ids_5(benchmark, run_async, session_factory, seeded_ids):
    """SELECT 5 products via IN-clause with prices + category loaded."""
    ids = seeded_ids["product_ids"][:5]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductRepository(session).get_by_ids(ids)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_get_by_ids_all(benchmark, run_async, session_factory, seeded_ids):
    """SELECT all 10 products via IN-clause with prices + category loaded."""
    ids = seeded_ids["product_ids"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductRepository(session).get_by_ids(ids)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_product_count(benchmark, run_async, session_factory):
    """COUNT(*) all products."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyProductRepository(session).count()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
