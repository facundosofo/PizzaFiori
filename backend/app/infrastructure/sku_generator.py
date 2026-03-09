"""
Generador de SKUs únicos para productos.
"""
import random
import re
from typing import Optional


def generar_sku_producto(nombre: str, categoria_nombre: Optional[str] = None) -> str:
    """
    Genera un SKU único para un producto.

    Formato: CAT-CLAVE-00000
    - CAT:   3 chars de la categoría (ej: PIZ, EMP, TAR)
    - CLAVE: hasta 5 chars del nombre — iniciales si hay múltiples ítems,
             primeras letras si es un solo término
    - 00000: 5 dígitos aleatorios para unicidad

    Ejemplos:
    - "Pizza Muzzarella"                              → PIZ-MUZZA-01234
    - "Empanada de Pollo"                             → EMP-POLLO-01234
    - "Picada: Tequeños, Nuggets y Papas Fritas"      → PIC-TNP-01234
    - "Tarta Jamón, Queso y Huevo (ENTERA)"           → TAR-JQHE-01234
    - "Tarta Jamón, Queso, Tomate y Huevo (PORCION)"  → TAR-JQTHP-01234
    """
    cat_base = normalizar_texto(categoria_nombre or "")
    cat_clean = re.sub(r"[^a-zA-Z0-9]", "", cat_base).upper()
    prefijo_cat = (cat_clean[:3] or "CAT").ljust(3, "X")

    clave_nombre = _extraer_clave_nombre(nombre)

    sufijo = f"{random.randint(0, 99999):05d}"
    return f"{prefijo_cat}-{clave_nombre}-{sufijo}"


def _extraer_clave_nombre(nombre: str) -> str:
    """
    Extrae una clave de hasta 5 chars del nombre del producto.

    1. Normaliza y elimina el prefijo de categoría del nombre.
    2. Extrae el primer char del contenido entre paréntesis (ENTERA→E, PORCION→P).
    3. Si quedan múltiples ítems (separados por coma o ' y '), usa la inicial de cada uno.
    4. Si es un solo término, usa sus primeros caracteres.
    """
    nombre_norm = normalizar_texto(nombre)
    nombre_sin_prefijo = _limpiar_prefijo_nombre(nombre_norm)

    # Extraer inicial del paréntesis y quitarlo del texto
    parenth_char = ""
    match = re.search(r"\(([^)]+)\)", nombre_sin_prefijo)
    if match:
        p = re.sub(r"[^a-zA-Z0-9]", "", normalizar_texto(match.group(1))).upper()
        if p:
            parenth_char = p[0]
        nombre_sin_prefijo = re.sub(r"\([^)]*\)", "", nombre_sin_prefijo).strip()

    max_base = 5 - len(parenth_char)  # reserva 1 char para el paréntesis si existe

    # Separar en ítems: primero por coma, luego por " y "
    comma_items = re.split(r",", nombre_sin_prefijo)
    tokens = []
    for item in comma_items:
        partes = re.split(r"\by\b", item.strip(), flags=re.IGNORECASE)
        tokens.extend(p.strip() for p in partes if p.strip())

    if len(tokens) <= 1:
        # Un solo término: primeros chars del texto limpio
        texto = tokens[0] if tokens else nombre_sin_prefijo
        clean = re.sub(r"[^a-zA-Z0-9]", "", texto).upper()
        base = clean[:max_base]
    else:
        # Múltiples ítems: inicial de la primera palabra de cada ítem
        initials = ""
        for token in tokens:
            palabras = token.split()
            if palabras:
                c = re.sub(r"[^a-zA-Z0-9]", "", normalizar_texto(palabras[0])).upper()
                if c:
                    initials += c[0]
        base = initials[:max_base]

    result = (base + parenth_char)[:5]
    return result or "PROD"


def _limpiar_prefijo_nombre(nombre: str) -> str:
    """Elimina el prefijo de categoría del nombre del producto para el cálculo del SKU."""
    patron = (
        r"^(?:"
        r"super\s+mila\s+|"
        r"pizza\s+de\s+|pizza\s+con\s+|pizza\s+|"
        r"empanada\s+de\s+|empanada\s+con\s+|empanada\s+|"
        r"tarta\s+|"
        r"papas\s+fritas\s+|papas\s+|"
        r"sandwich\s+de\s+mila\s+|sandwich\s+de\s+|sandwich\s+|"
        r"picada:\s*|picada\s+"
        r")"
    )
    return re.sub(patron, "", nombre, flags=re.IGNORECASE).strip()


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para usar en SKUs (quita acentos, ñ, etc.)."""
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N',
    }
    resultado = texto
    for original, reemplazo in reemplazos.items():
        resultado = resultado.replace(original, reemplazo)
    return resultado
