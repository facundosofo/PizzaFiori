"""
Generador de SKUs únicos para productos.
"""
import re
from typing import Optional


def generar_sku_producto(nombre: str, categoria_nombre: Optional[str] = None) -> str:
    """
    Genera un SKU único para un producto.
    
    Args:
        nombre: Nombre del producto
        categoria_nombre: Nombre de la categoría (opcional)
    
    Returns:
        SKU generado (ej: "PIZZ-MUZZ-001")
    
    TODO: Implementar lógica personalizada para generar SKUs legibles.
    Sugerencias:
    - Extraer primeras letras de categoría + producto
    - Normalizar caracteres especiales (ñ -> n, á -> a)
    - Agregar contador secuencial único
    - Validar que no exista en la BD antes de retornar
    
    Ejemplos:
    - Pizza Muzzarella -> PIZZ-MUZZ-001
    - Empanada Carne -> EMPA-CARN-001
    - Fainá Grande -> FAIN-GRAN-001
    """
    # Implementación temporal simple
    nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '', nombre.upper())[:8]
    return f"PROD-{nombre_limpio}-TEMP"


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para usar en SKUs (quita acentos, ñ, etc.).
    
    TODO: Implementar normalización completa de caracteres especiales.
    """
    # Reemplazos básicos
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    
    resultado = texto
    for original, reemplazo in reemplazos.items():
        resultado = resultado.replace(original, reemplazo)
    
    return resultado
