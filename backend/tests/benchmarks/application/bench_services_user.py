"""
bench_services_user.py — Benchmarks del UserService

NOTA: hash_password() usa bcrypt con 12 rounds — es lento por diseño.
Los benchmarks de registro/cambio de contraseña muestran esa latencia intencional.
Los demás benchmarks miden overhead del service sin bcrypt.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.user_service import UserService
from tests.helpers import build_user_model


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_uow(user=None, user_exists=False):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    default_user = user or build_user_model(id=1, username="testuser", role="USER")

    uow.users.get_by_id = AsyncMock(return_value=default_user)
    uow.users.get_by_username = AsyncMock(
        return_value=default_user if user_exists else None
    )
    uow.users.get_by_email = AsyncMock(return_value=None)  # sin conflicto de email
    uow.users.list = AsyncMock(return_value=[default_user])
    uow.users.list_by_role = AsyncMock(return_value=[default_user])
    uow.users.add = AsyncMock(return_value=None)
    uow.users.update = AsyncMock(return_value=None)
    uow.users.delete = AsyncMock(return_value=None)

    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    return uow


def _make_service(uow=None):
    audit = AsyncMock()
    audit.log_creation = AsyncMock(return_value=MagicMock(error=None))
    audit.log_update = AsyncMock(return_value=MagicMock(error=None))
    audit.log_deletion = AsyncMock(return_value=MagicMock(error=None))

    return UserService(
        uow=uow or _make_uow(),
        audit_service=audit,
        logger=MagicMock(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# register_user — bcrypt (lento por diseño)
# ══════════════════════════════════════════════════════════════════════════════

def bench_user_register(benchmark, run_async):
    """Registrar usuario nuevo (incluye bcrypt 12 rounds).
    
    Este benchmark confirma el tiempo esperado de hashing (~100–500ms).
    """
    service = _make_service()

    async def call():
        return await service.register_user(
            username=f"newuser",
            email="new@example.com",
            password="TestPass1",
            first_name="Test",
            last_name="User",
            created_by_username="admin",
        )

    benchmark.pedantic(
        lambda: run_async(call),
        iterations=1,
        rounds=5,  # pocas rondas: bcrypt es lento intencionalente
    )


# ══════════════════════════════════════════════════════════════════════════════
# authenticate_user — verificación bcrypt
# ══════════════════════════════════════════════════════════════════════════════

def bench_user_authenticate_success(benchmark, run_async):
    """Autenticar usuario con contraseña correcta (verify_password bcrypt).
    
    Mide la latencia real de bcrypt.verify — esperado ~100–500ms.
    """
    import bcrypt

    hashed = bcrypt.hashpw(b"TestPass1", bcrypt.gensalt(rounds=12)).decode()
    user = build_user_model(
        id=1,
        username="testuser",
        password_hash=hashed,
        failed_login_attempts=0,
        locked_until=None,
    )
    uow = _make_uow(user=user, user_exists=True)
    uow.users.get_by_username = AsyncMock(return_value=user)
    service = _make_service(uow)

    async def call():
        return await service.authenticate_user("testuser", "TestPass1")

    benchmark.pedantic(
        lambda: run_async(call),
        iterations=1,
        rounds=5,
    )


def bench_user_authenticate_wrong_password(benchmark, run_async):
    """Autenticar con contraseña incorrecta — igual latencia que éxito (bcrypt)."""
    import bcrypt

    hashed = bcrypt.hashpw(b"TestPass1", bcrypt.gensalt(rounds=12)).decode()
    user = build_user_model(
        id=1,
        username="testuser",
        password_hash=hashed,
        failed_login_attempts=0,
        locked_until=None,
    )
    uow = _make_uow(user=user, user_exists=True)
    uow.users.get_by_username = AsyncMock(return_value=user)
    service = _make_service(uow)

    async def call():
        return await service.authenticate_user("testuser", "WrongPass9")

    benchmark.pedantic(
        lambda: run_async(call),
        iterations=1,
        rounds=5,
    )


def bench_user_authenticate_locked(benchmark, run_async):
    """Autenticar usuario bloqueado — falla rápida, sin bcrypt."""
    from datetime import datetime, timedelta, timezone

    locked = build_user_model(
        id=1,
        username="lockeduser",
        locked_until=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    uow = _make_uow(user=locked, user_exists=True)
    uow.users.get_by_username = AsyncMock(return_value=locked)
    service = _make_service(uow)

    async def call():
        return await service.authenticate_user("lockeduser", "AnyPass1")

    benchmark(run_async, call)


def bench_user_authenticate_user_not_found(benchmark, run_async):
    """Autenticar usuario inexistente — falla rápida."""
    uow = _make_uow(user_exists=False)
    uow.users.get_by_username = AsyncMock(return_value=None)
    service = _make_service(uow)

    async def call():
        return await service.authenticate_user("nouser", "TestPass1")

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# get_user / get_all_users
# ══════════════════════════════════════════════════════════════════════════════

def bench_user_get_by_id(benchmark, run_async):
    """Obtener usuario por ID."""
    service = _make_service()

    async def call():
        return await service.get_user(1)

    benchmark(run_async, call)


def bench_user_get_all(benchmark, run_async):
    """Listar todos los usuarios."""
    service = _make_service()

    async def call():
        return await service.get_all_users(skip=0, limit=100)

    benchmark(run_async, call)


def bench_user_get_all_by_role(benchmark, run_async):
    """Listar usuarios filtrando por rol."""
    service = _make_service()

    async def call():
        return await service.get_all_users(skip=0, limit=100, role_filter="ADMIN")

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# update_user / change_password / delete / unlock
# ══════════════════════════════════════════════════════════════════════════════

def bench_user_update(benchmark, run_async):
    """Actualizar datos de perfil (sin cambio de contraseña)."""
    service = _make_service()

    async def call():
        return await service.update_user(
            1,
            {"first_name": "Nuevo", "last_name": "Apellido"},
            updated_by_username="admin",
        )

    benchmark(run_async, call)


def bench_user_change_password(benchmark, run_async):
    """Cambiar contraseña (verify + hash bcrypt).
    
    Mide 2 operaciones bcrypt: verify old + hash new.
    """
    import bcrypt

    hashed = bcrypt.hashpw(b"TestPass1", bcrypt.gensalt(rounds=12)).decode()
    user = build_user_model(id=1, password_hash=hashed)
    uow = _make_uow(user=user)
    service = _make_service(uow)

    async def call():
        return await service.change_password(1, "TestPass1", "NewPass2")

    benchmark.pedantic(
        lambda: run_async(call),
        iterations=1,
        rounds=5,
    )


def bench_user_delete(benchmark, run_async):
    """Eliminar usuario (hard delete)."""
    service = _make_service()

    async def call():
        return await service.delete_user(1, deleted_by_username="admin")

    benchmark(run_async, call)


def bench_user_unlock_account(benchmark, run_async):
    """Desbloquear cuenta de usuario."""
    service = _make_service()

    async def call():
        return await service.unlock_user_account(1, unlocked_by_username="admin")

    benchmark(run_async, call)


def bench_user_validate_password_valid(benchmark):
    """Validar contraseña válida (sync, sin bcrypt)."""
    service = _make_service()

    def call():
        return service.validate_password("TestPass1")

    benchmark(call)


def bench_user_validate_password_too_short(benchmark):
    """Validar contraseña demasiado corta (sync, sin bcrypt)."""
    service = _make_service()

    def call():
        return service.validate_password("abc")

    benchmark(call)
