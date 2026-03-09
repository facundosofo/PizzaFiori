"""
Seed script para PizzaFiori.
Ejecutar desde backend/: python seeds.py

Idempotente: verifica existencia antes de insertar.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

# Cargar .env explicitamente para que os.getenv() funcione
# (pydantic-settings NO popula os.environ, solo su propio modelo)
try:
    from dotenv import load_dotenv as _load_dotenv
    _env_file = Path(__file__).resolve().parent / ".env"
    if not _env_file.exists() and getattr(sys, 'frozen', False):
        _env_file = Path(sys.executable).resolve().parent.parent / ".env"
    _load_dotenv(dotenv_path=str(_env_file), override=False)
except Exception:
    pass  # Si dotenv no esta disponible, se usan las vars del sistema

# Importar modelos y DB
from app.infrastructure.database import AsyncSessionLocal
from app.domain.models.product_category import ProductCategory
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.models.offer import Offer
from app.domain.models.offer_item import OfferItem, oferta_item_productos
from app.domain.models.expense_category import ExpenseCategory
from app.domain.models.user import User
from app.infrastructure.sku_generator import generar_sku_producto, normalizar_texto
from app.application.user_service import hash_password

_log = logging.getLogger("seeds")


def _info(msg: str) -> None:
    """Escribe al logger Y a stdout (para ejecucion manual)."""
    _log.info(msg)
    try:
        print(msg)
    except Exception:
        pass  # stdout puede no estar disponible en contexto de servicio


# ─── Datos ───────────────────────────────────────────────────────────────────

CATEGORIAS_PRODUCTO = [
    "Pizzas",
    "Empanadas",
    "Super Milas",
    "Sandwich de Mila",
    "Papas Fritas",
    "Picada",
    "Tartas",
]

PRODUCTOS_POR_CATEGORIA = {
    "Pizzas": [
        "Muzzarella",
        "Napolitana",
        "Calabresa",
        "Roquefort",
        "Provolone",
        "Palmitos",
        "Ananá",
        "Anchoas",
        "Jamón y Morrones",
        "Espinaca S. Blanca",
        "Fugazza (S. Queso)",
        "Fugazetta",
        "Capresse",
        "Crudo y Rúcula",
        "Pizza Fiori",
        "Faina x Porción",
        "Faina Completa",
    ],
    "Empanadas": [
        "Carne",
        "Pollo",
        "Jamón y Queso",
        "Humita",
        "Capresse",
        "Verdura",
        "Roqueford",
        "Cebolla",
    ],
    "Super Milas": [
        "Napolitana",
        "Americana",
        "Fugazzetta",
        "Capresse",
    ],
    "Sandwich de Mila": [
        "Completo",
        "Simple",
    ],
    "Papas Fritas": [
        "Completas",
        "Simples",
    ],
    "Picada": [
        "Tequeños, Nuggets y Papas Fritas",
        "Tequeños",
    ],
    "Tartas": [
        "Jamón, Queso y Huevo (ENTERA)",
        "Jamón, Queso y Huevo (PORCION)",
        "Jamón, Queso, Tomate y Huevo (ENTERA)",
        "Jamón, Queso, Tomate y Huevo (PORCION)",
    ],
}

PRECIO_DEFAULT = Decimal("1000.00")

# Categorías de gastos: {padre: [hijos]}
GASTOS_CATEGORIAS = {
    "Materia Prima": ["Harina", "Muzzarella", "Especias"],
    "Sueldos": [],
    "Servicios": ["Luz", "Gas"],
    "Otros": [],
}

# Usuario base — credenciales leídas del .env (nunca en el código fuente)
USUARIO = {
    "username": os.getenv("SEED_ADMIN_USERNAME", "admin"),
    "email": os.getenv("SEED_ADMIN_EMAIL", "admin@pizzafiori.com.ar"),
    "first_name": os.getenv("SEED_ADMIN_FIRST_NAME", "Admin"),
    "last_name": os.getenv("SEED_ADMIN_LAST_NAME", "PizzaFiori"),
    "password": os.getenv("SEED_ADMIN_PASSWORD"),
    "role": "ADMIN",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def generar_sku_unico(nombre: str, categoria_nombre: str, contador: int = 0) -> str:
    """
    Genera un SKU único usando nombre + categoría para evitar colisiones
    entre productos con el mismo nombre en distintas categorías.
    Formato: PROD-{CAT3}{NOMBRE5}{##}-TEMP
    """
    cat_limpio = normalizar_texto(categoria_nombre.upper())
    cat_limpio = ''.join(c for c in cat_limpio if c.isalnum())[:3]

    nom_limpio = normalizar_texto(nombre.upper())
    nom_limpio = ''.join(c for c in nom_limpio if c.isalnum())[:5]

    return f"PROD-{cat_limpio}{nom_limpio}{contador:02d}-TEMP"


# ─── Seed functions ─────────────────────────────────────────────────────────

async def seed_product_categories(session) -> dict[str, ProductCategory]:
    """Crea categorias de producto. Retorna {nombre: ProductCategory}."""
    now = datetime.now()
    creados = 0
    resultado = {}

    for nombre in CATEGORIAS_PRODUCTO:
        stmt = select(ProductCategory).where(ProductCategory.nombre == nombre)
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            resultado[nombre] = existing
            _info(f"  [SKIP] Categoria producto: {nombre} (ya existe, id={existing.id})")
        else:
            cat = ProductCategory(
                nombre=nombre,
                activo=True,
                fecha_creacion=now,
                fecha_actualizacion=now,
            )
            session.add(cat)
            resultado[nombre] = cat
            creados += 1

    await session.flush()
    _info(f"  -> Categorias producto: {creados} creadas, {len(CATEGORIAS_PRODUCTO) - creados} existentes")
    return resultado


async def seed_products(session, categorias: dict[str, ProductCategory]) -> dict[str, Product]:
    """Crea productos con precio unitario. Retorna {(categoria, nombre): Product}."""
    now = datetime.now()
    creados = 0
    total = 0
    resultado = {}
    skus_usados = set()

    for cat_nombre, productos in PRODUCTOS_POR_CATEGORIA.items():
        categoria = categorias[cat_nombre]

        for prod_nombre in productos:
            total += 1
            # Generar SKU unico con contador incremental para evitar colisiones
            contador = 0
            sku = generar_sku_unico(prod_nombre, cat_nombre, contador)
            while sku in skus_usados:
                contador += 1
                sku = generar_sku_unico(prod_nombre, cat_nombre, contador)
            skus_usados.add(sku)

            # Verificar por nombre + categoria (mas fiable que SKU)
            stmt = select(Product).where(
                Product.nombre == prod_nombre,
                Product.categoria_id == categoria.id,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            # Si no existe por nombre, verificar por SKU
            if not existing:
                stmt2 = select(Product).where(Product.sku == sku)
                existing = (await session.execute(stmt2)).scalar_one_or_none()

            if existing:
                resultado[f"{cat_nombre}::{prod_nombre}"] = existing
                _info(f"  [SKIP] Producto: {prod_nombre} ({cat_nombre}) (ya existe, id={existing.id})")
            else:
                producto = Product(
                    sku=sku,
                    nombre=prod_nombre,
                    categoria_id=categoria.id,
                    activo=True,
                    fecha_creacion=now,
                    fecha_actualizacion=now,
                    precios=[
                        ProductPrice(
                            cantidad=1,
                            precio=PRECIO_DEFAULT,
                            fecha_creacion=now,
                            fecha_actualizacion=now,
                        )
                    ],
                )
                session.add(producto)
                resultado[f"{cat_nombre}::{prod_nombre}"] = producto
                creados += 1

    await session.flush()
    _info(f"  -> Productos: {creados} creados, {total - creados} existentes")
    return resultado


async def seed_offers(session, categorias: dict[str, ProductCategory], productos: dict[str, Product]):
    """Crea las 4 promos."""
    now = datetime.now()
    creados = 0

    ofertas_def = [
        {
            "nombre": "PROMO 1",
            "descripcion": "3 Muzzarella",
            "precio": PRECIO_DEFAULT,
            "items": [
                {
                    "tipo": "producto",
                    "producto_key": "Pizzas::Muzzarella",
                    "cantidad": 3,
                },
            ],
        },
        {
            "nombre": "PROMO 2",
            "descripcion": "2 Docenas de Empanadas",
            "precio": PRECIO_DEFAULT,
            "items": [
                {
                    "tipo": "categoria",
                    "categoria_nombre": "Empanadas",
                    "cantidad": 24,
                },
            ],
        },
        {
            "nombre": "PROMO 3",
            "descripcion": "1 Especial + 1 Muzzarella + 6 Empanadas",
            "precio": PRECIO_DEFAULT,
            "items": [
                {
                    "tipo": "opciones",
                    "producto_keys": [
                        "Pizzas::Jamón y Morrones",
                        "Pizzas::Napolitana",
                        "Pizzas::Calabresa",
                    ],
                    "cantidad": 1,
                },
                {
                    "tipo": "producto",
                    "producto_key": "Pizzas::Muzzarella",
                    "cantidad": 1,
                },
                {
                    "tipo": "categoria",
                    "categoria_nombre": "Empanadas",
                    "cantidad": 6,
                },
            ],
        },
        {
            "nombre": "PROMO 4",
            "descripcion": "1 Muzzarella + 6 Empanadas",
            "precio": PRECIO_DEFAULT,
            "items": [
                {
                    "tipo": "producto",
                    "producto_key": "Pizzas::Muzzarella",
                    "cantidad": 1,
                },
                {
                    "tipo": "categoria",
                    "categoria_nombre": "Empanadas",
                    "cantidad": 6,
                },
            ],
        },
    ]

    for oferta_def in ofertas_def:
        nombre = oferta_def["nombre"]

        stmt = select(Offer).where(Offer.nombre == nombre)
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            _info(f"  [SKIP] Oferta: {nombre} (ya existe, id={existing.id})")
            continue

        items = []
        for item_def in oferta_def["items"]:
            if item_def["tipo"] == "producto":
                producto = productos[item_def["producto_key"]]
                offer_item = OfferItem(
                    cantidad=item_def["cantidad"],
                )
                offer_item.productos = [producto]
                items.append(offer_item)

            elif item_def["tipo"] == "categoria":
                cat = categorias[item_def["categoria_nombre"]]
                offer_item = OfferItem(
                    categoria_id=cat.id,
                    cantidad=item_def["cantidad"],
                )
                items.append(offer_item)

            elif item_def["tipo"] == "opciones":
                prods = [productos[k] for k in item_def["producto_keys"]]
                offer_item = OfferItem(
                    cantidad=item_def["cantidad"],
                )
                offer_item.productos = prods
                items.append(offer_item)

        oferta = Offer(
            nombre=nombre,
            descripcion=oferta_def["descripcion"],
            precio=oferta_def["precio"],
            activo=True,
            fecha_creacion=now,
            fecha_actualizacion=now,
            productos=items,
        )
        session.add(oferta)
        creados += 1

    await session.flush()
    _info(f"  -> Ofertas: {creados} creadas, {len(ofertas_def) - creados} existentes")


async def seed_expense_categories(session):
    """Crea categorias y subcategorias de gastos."""
    now = datetime.now()
    creados_padres = 0
    creados_hijos = 0

    padres = {}

    # Crear padres
    for padre_nombre in GASTOS_CATEGORIAS:
        stmt = select(ExpenseCategory).where(
            ExpenseCategory.nombre == padre_nombre,
            ExpenseCategory.padre_id.is_(None),
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            padres[padre_nombre] = existing
            _info(f"  [SKIP] Gasto categoria padre: {padre_nombre} (ya existe, id={existing.id})")
        else:
            cat = ExpenseCategory(
                nombre=padre_nombre,
                padre_id=None,
                activo=True,
                fecha_creacion=now,
                fecha_actualizacion=now,
            )
            session.add(cat)
            padres[padre_nombre] = cat
            creados_padres += 1

    await session.flush()

    # Crear hijos
    for padre_nombre, hijos in GASTOS_CATEGORIAS.items():
        padre = padres[padre_nombre]
        for hijo_nombre in hijos:
            stmt = select(ExpenseCategory).where(
                ExpenseCategory.nombre == hijo_nombre,
                ExpenseCategory.padre_id == padre.id,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            if existing:
                _info(f"  [SKIP] Gasto subcategoria: {hijo_nombre} -> {padre_nombre} (ya existe, id={existing.id})")
            else:
                sub = ExpenseCategory(
                    nombre=hijo_nombre,
                    padre_id=padre.id,
                    activo=True,
                    fecha_creacion=now,
                    fecha_actualizacion=now,
                )
                session.add(sub)
                creados_hijos += 1

    await session.flush()
    total_hijos = sum(len(h) for h in GASTOS_CATEGORIAS.values())
    _info(f"  -> Gastos categorias padre: {creados_padres} creadas, {len(GASTOS_CATEGORIAS) - creados_padres} existentes")
    _info(f"  -> Gastos subcategorias: {creados_hijos} creadas, {total_hijos - creados_hijos} existentes")


async def seed_users(session):
    """Crea el usuario ADMIN base."""
    username = USUARIO["username"]

    stmt = select(User).where(User.username == username)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        _info(f"  [SKIP] Usuario: {username} (ya existe, id={existing.id})")
        return

    now = datetime.now()
    password_hash = hash_password(USUARIO["password"])

    user = User(
        username=username,
        email=USUARIO["email"],
        password_hash=password_hash,
        first_name=USUARIO["first_name"],
        last_name=USUARIO["last_name"],
        role=USUARIO["role"],
        failed_login_attempts=0,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    await session.flush()
    _info(f"  -> Usuario: {username} creado (role={USUARIO['role']}, id={user.id})")


# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    if not USUARIO["password"]:
        raise EnvironmentError("SEED_ADMIN_PASSWORD no esta definida en el .env")

    _info("=" * 60)
    _info("  PizzaFiori - Seed de datos iniciales")
    _info("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            # Transaccion explicita — NO usar session.begin() como context manager
            # para tener control total sobre commit/rollback
            await session.begin()

            _info("[1/5] Categorias de producto...")
            categorias = await seed_product_categories(session)

            _info("[2/5] Productos...")
            productos = await seed_products(session, categorias)

            _info("[3/5] Ofertas (Promos)...")
            await seed_offers(session, categorias, productos)

            _info("[4/5] Categorias de gastos...")
            await seed_expense_categories(session)

            _info("[5/5] Usuarios...")
            await seed_users(session)

            # Commit explicito con confirmacion
            await session.commit()
            _info("=" * 60)
            _info("  Seed completado y COMMIT exitoso!")
            _info("=" * 60)

        except Exception as e:
            await session.rollback()
            _log.error("Seed fallo: %s", e, exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(main())
