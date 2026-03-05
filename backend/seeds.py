"""
Seed script para PizzaFiori.
Ejecutar desde backend/: python seeds.py

Idempotente: verifica existencia antes de insertar.
"""

import asyncio
import sys
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

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

# Usuario base
USUARIO = {
    "username": "FacundoS",
    "email": "facundosofo@gmail.com",
    "first_name": "Facundo",
    "last_name": "Sofia",
    "password": "FacundoS123++",
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
    """Crea categorías de producto. Retorna {nombre: ProductCategory}."""
    now = datetime.now()
    creados = 0
    resultado = {}

    for nombre in CATEGORIAS_PRODUCTO:
        stmt = select(ProductCategory).where(ProductCategory.nombre == nombre)
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            resultado[nombre] = existing
            print(f"  [SKIP] Categoría producto: {nombre} (ya existe, id={existing.id})")
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
    print(f"  → Categorías producto: {creados} creadas, {len(CATEGORIAS_PRODUCTO) - creados} existentes")
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
            # Generar SKU único con contador incremental para evitar colisiones
            contador = 0
            sku = generar_sku_unico(prod_nombre, cat_nombre, contador)
            while sku in skus_usados:
                contador += 1
                sku = generar_sku_unico(prod_nombre, cat_nombre, contador)
            skus_usados.add(sku)

            # Verificar por nombre + categoría (más fiable que SKU)
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
                print(f"  [SKIP] Producto: {prod_nombre} ({cat_nombre}) (ya existe, id={existing.id})")
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
    print(f"  → Productos: {creados} creados, {total - creados} existentes")
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
            print(f"  [SKIP] Oferta: {nombre} (ya existe, id={existing.id})")
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
    print(f"  → Ofertas: {creados} creadas, {len(ofertas_def) - creados} existentes")


async def seed_expense_categories(session):
    """Crea categorías y subcategorías de gastos."""
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
            print(f"  [SKIP] Gasto categoría padre: {padre_nombre} (ya existe, id={existing.id})")
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
                print(f"  [SKIP] Gasto subcategoría: {hijo_nombre} → {padre_nombre} (ya existe, id={existing.id})")
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
    print(f"  → Gastos categorías padre: {creados_padres} creadas, {len(GASTOS_CATEGORIAS) - creados_padres} existentes")
    print(f"  → Gastos subcategorías: {creados_hijos} creadas, {total_hijos - creados_hijos} existentes")


async def seed_users(session):
    """Crea el usuario ADMIN base."""
    username = USUARIO["username"]

    stmt = select(User).where(User.username == username)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        print(f"  [SKIP] Usuario: {username} (ya existe, id={existing.id})")
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
    print(f"  → Usuario: {username} creado (role={USUARIO['role']}, id={user.id})")


# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("  PizzaFiori - Seed de datos iniciales")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                print("[1/5] Categorías de producto...")
                categorias = await seed_product_categories(session)
                print()

                print("[2/5] Productos...")
                productos = await seed_products(session, categorias)
                print()

                print("[3/5] Ofertas (Promos)...")
                await seed_offers(session, categorias, productos)
                print()

                print("[4/5] Categorías de gastos...")
                await seed_expense_categories(session)
                print()

                print("[5/5] Usuarios...")
                await seed_users(session)
                print()

                # session.begin() hace commit automático al salir del context manager
                print("=" * 60)
                print("  Seed completado exitosamente!")
                print("=" * 60)

            except Exception as e:
                print(f"\n[ERROR] Seed falló: {e}")
                raise


if __name__ == "__main__":
    asyncio.run(main())
