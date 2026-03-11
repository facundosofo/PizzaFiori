"""
Repository-layer DB benchmarks: category stock and order daily sequence.

Data seeded: 2 stock records (one per product category), 7 sequence records
(one per day for the past week).
Uses benchmark.pedantic with rounds=50, iterations=3 for deterministic stats.

Note: bench_db_sequence_get_for_update issues SELECT FOR UPDATE. The row lock
is released automatically when the session context manager exits without commit.
"""

from datetime import timedelta

from app.infrastructure.repositories.category_stock_repository import (
    SqlAlchemyCategoryStockRepository,
)
from app.infrastructure.repositories.sequence_repository import SqlAlchemySequenceRepository


# ── CategoryStock ─────────────────────────────────────────────────────────────

def bench_db_stock_get_all(benchmark, run_async, session_factory):
    """SELECT all category stock records."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyCategoryStockRepository(session).get_all()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_stock_get_by_categoria_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single stock record by category FK (primary key lookup)."""
    cat_id = seeded_ids["cat_pizzas_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyCategoryStockRepository(session).get_by_categoria_id(cat_id)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


# ── OrderDailySequence ────────────────────────────────────────────────────────

def bench_db_sequence_get_for_update_today(benchmark, run_async, session_factory, seeded_ids):
    """SELECT ... FOR UPDATE on today's sequence row (advisory row-level lock)."""
    today = seeded_ids["first_sequence_date"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySequenceRepository(session).get_for_update(today)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_sequence_get_for_update_yesterday(benchmark, run_async, session_factory, seeded_ids):
    """SELECT ... FOR UPDATE on yesterday's sequence row."""
    yesterday = seeded_ids["first_sequence_date"] - timedelta(days=1)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemySequenceRepository(session).get_for_update(yesterday)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
