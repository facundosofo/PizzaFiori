"""
Repository-layer DB benchmarks: audit log.

Data seeded: 40 audit records spanning 5 entity types (Product, Sale, Expense,
User, Offer), 3 action types (CREATE, UPDATE, DELETE), and 6 users
(bench_admin + bench_user_1..5), spread across the past 10 days.
Uses benchmark.pedantic with rounds=50, iterations=3 for deterministic stats.
"""

from datetime import datetime, timedelta

from app.infrastructure.repositories.audit_repository import SqlAlchemyAuditRepository


def bench_db_audit_get_by_date_range_10d(benchmark, run_async, session_factory):
    """SELECT all 40 audit logs in the last 10 days (no entity filter)."""
    end = datetime.now()
    start = end - timedelta(days=10)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).get_by_date_range(
                start_date=start, end_date=end, limit=100
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_get_by_date_range_entity_filter(benchmark, run_async, session_factory):
    """SELECT audit logs filtered by entity_type='Product' (~8 of 40 records)."""
    end = datetime.now()
    start = end - timedelta(days=10)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).get_by_date_range(
                start_date=start, end_date=end, entity_type="Product", limit=100
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_get_by_date_range_username_filter(benchmark, run_async, session_factory):
    """SELECT audit logs filtered by username='bench_admin' (~14 of 40 records)."""
    end = datetime.now()
    start = end - timedelta(days=10)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).get_by_date_range(
                start_date=start, end_date=end, username="bench_admin", limit=100
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_get_by_date_range_action_filter(benchmark, run_async, session_factory):
    """SELECT audit logs filtered by action='CREATE' (~14 of 40 records)."""
    end = datetime.now()
    start = end - timedelta(days=10)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).get_by_date_range(
                start_date=start, end_date=end, action="CREATE", limit=100
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_get_by_entity(benchmark, run_async, session_factory, seeded_ids):
    """SELECT audit logs for a specific entity_type + entity_id combination."""
    entity_id = seeded_ids["first_audit_entity_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).get_by_entity(
                entity_type="Product", entity_id=entity_id
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single audit log by PK."""
    aid = seeded_ids["first_audit_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).get_by_id(aid)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_count(benchmark, run_async, session_factory):
    """COUNT(*) all audit logs."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).count()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_count_with_entity_filter(benchmark, run_async, session_factory):
    """COUNT(*) audit logs filtered by entity_type='Product'."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).count(entity_type="Product")

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_audit_count_with_date_filter(benchmark, run_async, session_factory):
    """COUNT(*) audit logs in the last 5 days."""
    end = datetime.now()
    start = end - timedelta(days=5)

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyAuditRepository(session).count(
                start_date=start, end_date=end
            )

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
