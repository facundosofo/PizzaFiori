"""
Repository-layer DB benchmarks: users.

Data seeded: 1 ADMIN + 5 USER accounts (6 total).
Uses benchmark.pedantic with rounds=50, iterations=3 for deterministic stats.
"""

from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


def bench_db_user_list_all(benchmark, run_async, session_factory):
    """SELECT all users (limit 100)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyUserRepository(session).list(skip=0, limit=100)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_user_list_by_role_admin(benchmark, run_async, session_factory):
    """SELECT users with role=ADMIN (1 result)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyUserRepository(session).list_by_role("ADMIN")

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_user_list_by_role_user(benchmark, run_async, session_factory):
    """SELECT users with role=USER (5 results)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyUserRepository(session).list_by_role("USER")

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_user_get_by_id(benchmark, run_async, session_factory, seeded_ids):
    """SELECT single user by PK."""
    uid = seeded_ids["admin_user_id"]

    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyUserRepository(session).get_by_id(uid)

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_user_get_by_username(benchmark, run_async, session_factory):
    """SELECT user by username (indexed lookup)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyUserRepository(session).get_by_username("bench_admin")

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_user_get_by_email(benchmark, run_async, session_factory):
    """SELECT user by email (indexed lookup)."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyUserRepository(session).get_by_email("bench_admin@benchmark.test")

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)


def bench_db_user_count(benchmark, run_async, session_factory):
    """COUNT(*) all users."""
    async def _call():
        async with session_factory() as session:
            return await SqlAlchemyUserRepository(session).count()

    benchmark.pedantic(run_async, args=(_call,), rounds=50, iterations=3, warmup_rounds=3)
