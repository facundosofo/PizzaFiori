"""
Repository-layer DB benchmarks: sales.

Each benchmark iteration creates a fresh AsyncSession (per-request lifecycle).
Measures paginated lists, date-filtered queries, COUNTs, and single-record
lookups with deeply nested selectinload chains.
Data: 50 sales, 2 items each (100 SaleItem rows total).
"""

from datetime import datetime, timedelta

from app.infrastructure.repositories.sale_repository import SqlAlchemySaleRepository


def bench_db_sale_list_20(benchmark, run_async, session_factory):
    """SELECT first 20 sales with full item + product selectinload."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).list(skip=0, limit=20)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sale_list_50(benchmark, run_async, session_factory):
    """SELECT all 50 sales with full item + product selectinload."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).list(skip=0, limit=50)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sale_list_paginated_offset(benchmark, run_async, session_factory):
    """SELECT sales page 2 (OFFSET 20 LIMIT 20)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).list(skip=20, limit=20)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sale_list_with_date_filter_30d(benchmark, run_async, session_factory):
    """SELECT sales in last 30 days (business-date adjusted -6h)."""
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=30)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).list(
                skip=0,
                limit=50,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sale_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single sale by PK with all nested items loaded."""
    sid = seeded_ids["first_sale_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).get_by_id(sid)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sale_count(benchmark, run_async, session_factory):
    """COUNT(*) all sales."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).count()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sale_count_with_date_filter(benchmark, run_async, session_factory):
    """COUNT(*) sales filtered by date range (last 30 days)."""
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=30)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).count(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sale_get_distinct_years(benchmark, run_async, session_factory):
    """SELECT DISTINCT years from sales (business-date adjusted)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySaleRepository(session).get_distinct_years()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
