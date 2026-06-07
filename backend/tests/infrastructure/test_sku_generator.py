"""
Tests unitarios para el generador de SKUs.

Formato de SKU: CAT-CLAVE-NNNNN
  - CAT   = 3 chars de la categoría
  - CLAVE = hasta 5 chars derivados del nombre (parte determinista)
  - NNNNN = 5 dígitos aleatorios

Los tests verifican la parte fija (CAT-CLAVE), ignorando el sufijo aleatorio.
"""

import re
import pytest
from app.infrastructure.sku_generator import generar_sku_producto, normalizar_texto


# ─── Helper ──────────────────────────────────────────────────────────────────

def parte_fija(nombre: str, categoria: str) -> str:
    """Retorna solo CAT-CLAVE (sin el sufijo aleatorio -NNNNN)."""
    sku = generar_sku_producto(nombre, categoria)
    return sku.rsplit("-", 1)[0]


# ─── Estructura general ───────────────────────────────────────────────────────

def test_formato_sku():
    """SKU debe tener formato XXX-XXXXX-00000."""
    sku = generar_sku_producto("Empanada de Carne", "Empanadas")
    assert re.fullmatch(r"[A-Z0-9]{3}-[A-Z0-9]{1,5}-\d{5}", sku), f"Formato inesperado: {sku}"


def test_sku_es_string_mayusculas():
    sku = generar_sku_producto("empanada de carne", "empanadas")
    assert isinstance(sku, str)
    assert sku == sku.upper()


def test_sin_categoria():
    sku = generar_sku_producto("Producto Test", None)
    assert sku is not None
    assert len(sku) > 0


def test_nombre_largo_no_desborda():
    sku = generar_sku_producto(
        "Empanada de Carne con Cebolla Picada y Condimentos Especiales", "Empanadas"
    )
    assert len(sku) < 20


# ─── Pizzas ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Pizza Muzzarella",          "PIZ-MUZZA"),
    ("Pizza Napolitana",          "PIZ-NAPOL"),
    ("Pizza Calabresa",           "PIZ-CALAB"),
    ("Pizza Roquefort",           "PIZ-ROQUE"),
    ("Pizza Provolone",           "PIZ-PROVO"),
    ("Pizza Palmitos",            "PIZ-PALMI"),
    ("Pizza Ananá",               "PIZ-ANANA"),
    ("Pizza Anchoas",             "PIZ-ANCHO"),
    ("Pizza Jamón y Morrones",    "PIZ-JAMOM"),   # 3 palabras → JAM+O+M
    ("Pizza Espinaca S. Blanca",  "PIZ-ESPSB"),   # 3 palabras → ESP+S+B
    ("Pizza Fugazza (S. Queso)",  "PIZ-FUGAS"),   # parenth=S, max_base=4 → FUGA+S
    ("Pizza Fugazetta",           "PIZ-FUGAZ"),
    ("Pizza Caprese",             "PIZ-CAPRE"),
    ("Pizza Crudo y Rúcula",      "PIZ-CRUDR"),   # 3 palabras → CRU+D+R
    ("Pizza Fiori",               "PIZ-FIORI"),
    ("Faina (Porcion)",           "PIZ-FAINP"),   # parenth=P → FAIN+P
    ("Faina Completa",            "PIZ-FAINC"),   # 2 palabras → FAIN+C
])
def test_pizzas(nombre, esperado):
    assert parte_fija(nombre, "Pizzas") == esperado


# ─── Empanadas ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Empanada de Carne",         "EMP-CARNE"),
    ("Empanada de Pollo",         "EMP-POLLO"),
    ("Empanada de Jamón y Queso", "EMP-JAMOQ"),   # 3 palabras → JAM+O+Q
    ("Empanada de Humita",        "EMP-HUMIT"),
    ("Empanada Caprese",          "EMP-CAPRE"),
    ("Empanada de Verdura",       "EMP-VERDU"),
    ("Empanada de Roquefort",     "EMP-ROQUE"),
    ("Empanada de Cebolla",       "EMP-CEBOL"),
])
def test_empanadas(nombre, esperado):
    assert parte_fija(nombre, "Empanadas") == esperado


# ─── Super Milas ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Super Mila Napolitana",  "SUP-NAPOL"),
    ("Super Mila Americana",   "SUP-AMERI"),
    ("Super Mila Fugazzetta",  "SUP-FUGAZ"),
    ("Super Mila Caprese",     "SUP-CAPRE"),
])
def test_super_milas(nombre, esperado):
    assert parte_fija(nombre, "Super Milas") == esperado


# ─── Sandwich de Mila ────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Sandwich de Mila Completo", "SAN-COMPL"),
    ("Sandwich de Mila Simple",   "SAN-SIMPL"),
])
def test_sandwich_de_mila(nombre, esperado):
    assert parte_fija(nombre, "Sandwich de Mila") == esperado


# ─── Papas Fritas ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Papas Fritas Completas", "PAP-COMPL"),
    ("Papas Fritas Simples",   "PAP-SIMPL"),
])
def test_papas_fritas(nombre, esperado):
    assert parte_fija(nombre, "Papas Fritas") == esperado


# ─── Picada ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Picada: Tequeños, Nuggets y Papas Fritas", "PIC-TEQNP"),  # tokens=3 → TEQ+N+P
    ("Picada: Tequeños",                         "PIC-TEQUE"),
])
def test_picada(nombre, esperado):
    assert parte_fija(nombre, "Picada") == esperado


# ─── Tartas ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Jamón, Queso y Huevo",                    "TAR-JAMQH"),   # 3 tokens → JAM+Q+H
    ("Jamón, Queso y Huevo (PORCION)",           "TAR-JAQHP"),   # parenth=P, max_base=4, 3 tokens → JA+Q+H+P
    ("Jamón, Queso, Tomate y Huevo",             "TAR-JAQTH"),   # 4 tokens → JA+Q+T+H
    ("Jamón, Queso, Tomate y Huevo (PORCION)",   "TAR-JQTHP"),   # parenth=P, max_base=4, 4 tokens → J+Q+T+H+P
])
def test_tartas(nombre, esperado):
    assert parte_fija(nombre, "Tartas") == esperado


# ─── Extras ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre,esperado", [
    ("Salsa",            "EXT-SALSA"),
    ("Muzzarella",       "EXT-MUZZA"),
    ("Aceitunas Verdes", "EXT-ACEIV"),   # 2 palabras → ACEI+V
    ("Aceitunas Negras", "EXT-ACEIN"),   # 2 palabras → ACEI+N  (no colisión con Verdes)
    ("Jamón",            "EXT-JAMON"),
    ("Huevo Frito",      "EXT-HUEVF"),   # 2 palabras → HUEV+F
])
def test_extras(nombre, esperado):
    assert parte_fija(nombre, "Extras") == esperado


# ─── Sin colisiones dentro de cada categoría ────────────────────────────────

def test_sin_colisiones_pizzas():
    claves = [parte_fija(n, "Pizzas") for n in [
        "Pizza Muzzarella","Pizza Napolitana","Pizza Calabresa","Pizza Roquefort",
        "Pizza Provolone","Pizza Palmitos","Pizza Ananá","Pizza Anchoas",
        "Pizza Jamón y Morrones","Pizza Espinaca S. Blanca","Pizza Fugazza (S. Queso)",
        "Pizza Fugazetta","Pizza Caprese","Pizza Crudo y Rúcula","Pizza Fiori",
        "Faina (Porcion)","Faina Completa",
    ]]
    assert len(claves) == len(set(claves)), f"Colisiones detectadas: {claves}"


def test_sin_colisiones_tartas():
    claves = [parte_fija(n, "Tartas") for n in [
        "Jamón, Queso y Huevo",
        "Jamón, Queso y Huevo (PORCION)",
        "Jamón, Queso, Tomate y Huevo",
        "Jamón, Queso, Tomate y Huevo (PORCION)",
    ]]
    assert len(claves) == len(set(claves)), f"Colisiones detectadas: {claves}"


def test_sin_colisiones_extras():
    claves = [parte_fija(n, "Extras") for n in [
        "Salsa","Muzzarella","Aceitunas Verdes","Aceitunas Negras","Jamón","Huevo Frito",
    ]]
    assert len(claves) == len(set(claves)), f"Colisiones detectadas: {claves}"


# ─── normalizar_texto ─────────────────────────────────────────────────────────

def test_normalizar_texto_vocales():
    assert normalizar_texto("áéíóú") == "aeiou"
    assert normalizar_texto("ÁÉÍÓÚ") == "AEIOU"


def test_normalizar_texto_enie():
    assert normalizar_texto("niño") == "nino"
    assert normalizar_texto("NIÑO") == "NINO"


def test_normalizar_texto_sin_cambios():
    assert normalizar_texto("Pizza Muzza") == "Pizza Muzza"


def test_normalizar_texto_vacio():
    assert normalizar_texto("") == ""
