"""
Repository-layer DB benchmarks: expenses, expense categories, offers.

Each benchmark iteration creates a fresh AsyncSession (per-request lifecycle).
Measures filter-heavy expense queries, hierarchical category lookups, and
offer queries with multi-level nested selectinloads.
Data: 4 expense categories (2 root, 2 sub), 30 expenses, 1 offer with 2 items.
"""

from datetime import date, timedelta

from app.infrastructure.repositories.expense_category_repository import (
    SqlAlchemyExpenseCategoryRepository,
)
from app.infrastructure.repositories.expense_repository import SqlAlchemyExpenseRepository
from app.infrastructure.repositories.offer_repository import SqlAlchemyOfferRepository


# ── Expense ───────────────────────────────────────────────────────────────────

def bench_db_expense_list_all(benchmark, run_async, session_factory):
    """SELECT all active expenses (no filters)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseRepository(session).list()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_list_by_category(benchmark, run_async, session_factory, seeded_ids):
    """SELECT expenses filtered by category ID."""
    cat_id = seeded_ids["expense_cat_sub_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseRepository(session).list_by_filters(
                categoria_gasto_ids=[cat_id]
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_list_by_date_30d(benchmark, run_async, session_factory):
    """SELECT expenses in last 30 days."""
    fecha_hasta = date.today()
    fecha_desde = fecha_hasta - timedelta(days=30)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseRepository(session).list_by_filters(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_list_by_date_and_category(benchmark, run_async, session_factory, seeded_ids):
    """SELECT expenses with combined date + category filters."""
    cat_id = seeded_ids["expense_cat_sub_id"]
    fecha_hasta = date.today()
    fecha_desde = fecha_hasta - timedelta(days=60)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseRepository(session).list_by_filters(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                categoria_gasto_ids=[cat_id],
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single expense by PK."""
    eid = seeded_ids["first_expense_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseRepository(session).get_by_id(eid)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_count(benchmark, run_async, session_factory):
    """COUNT(*) all expenses."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseRepository(session).count()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


# ── ExpenseCategory ───────────────────────────────────────────────────────────

def bench_db_expense_category_list_all(benchmark, run_async, session_factory):
    """SELECT all expense categories."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseCategoryRepository(session).list()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_category_list_active(benchmark, run_async, session_factory):
    """SELECT active expense categories only."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseCategoryRepository(session).list_by_active(activo=True)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_category_get_roots(benchmark, run_async, session_factory):
    """SELECT root categories (padre_id IS NULL)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseCategoryRepository(session).get_by_parent_id(None)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_expense_category_get_children(benchmark, run_async, session_factory, seeded_ids):
    """SELECT children of a given category."""
    parent_id = seeded_ids["expense_cat_root_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyExpenseCategoryRepository(session).get_by_parent_id(parent_id)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


# ── Offer ─────────────────────────────────────────────────────────────────────

def bench_db_offer_list_all(benchmark, run_async, session_factory):
    """SELECT all offers with nested items + products + categories."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyOfferRepository(session).list()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_offer_list_active(benchmark, run_async, session_factory):
    """SELECT active offers only."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyOfferRepository(session).list(active=True)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_offer_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single offer by PK with full nested selectinload."""
    oid = seeded_ids["offer_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyOfferRepository(session).get_by_id(oid)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
