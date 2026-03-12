"""
Migración de imágenes existentes: redimensiona y comprime los JPEGs en uploads/productos/.

Uso:
    python resize_uploads.py            # procesa todos los archivos
    python resize_uploads.py --dry-run  # solo muestra qué haría, sin modificar nada

Requiere Pillow:
    pip install Pillow
"""
import argparse
import io
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow no está instalado. Ejecuta: pip install Pillow")
    sys.exit(1)

MAX_PX = 800
QUALITY = 80
UPLOADS_DIR = Path(__file__).parent / "uploads" / "productos"


def human_size(n: int) -> str:
    return f"{n / 1024:.1f} KB" if n < 1_048_576 else f"{n / 1_048_576:.1f} MB"


def process_image(path: Path, dry_run: bool) -> tuple[int, int]:
    """Devuelve (tamaño_original, tamaño_nuevo) en bytes."""
    original_size = path.stat().st_size
    data = path.read_bytes()

    try:
        img = Image.open(io.BytesIO(data))
    except Exception as e:
        print(f"  SKIP  {path.name}: no se pudo abrir como imagen ({e})")
        return original_size, original_size

    if img.mode != "RGB":
        img = img.convert("RGB")

    needs_resize = img.width > MAX_PX or img.height > MAX_PX
    orig_dims = f"{img.width}×{img.height}"

    if needs_resize:
        img.thumbnail((MAX_PX, MAX_PX), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=QUALITY, optimize=True)
    new_data = buf.getvalue()
    new_size = len(new_data)

    savings_pct = (1 - new_size / original_size) * 100 if original_size > 0 else 0
    resize_info = f"{orig_dims} → {img.width}×{img.height}" if needs_resize else f"{orig_dims} (sin resize)"
    print(
        f"  {'(dry) ' if dry_run else ''}  {path.name:40s}  "
        f"{human_size(original_size):>10s} → {human_size(new_size):>10s}  "
        f"(-{savings_pct:.0f}%)  {resize_info}"
    )

    if not dry_run:
        path.write_bytes(new_data)

    return original_size, new_size


def main():
    parser = argparse.ArgumentParser(description="Redimensiona y comprime imágenes de productos")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra los cambios sin escribir")
    args = parser.parse_args()

    if not UPLOADS_DIR.exists():
        print(f"ERROR: No se encontró el directorio {UPLOADS_DIR}")
        sys.exit(1)

    images = sorted(UPLOADS_DIR.glob("*.jpg")) + sorted(UPLOADS_DIR.glob("*.jpeg")) + sorted(UPLOADS_DIR.glob("*.png"))
    if not images:
        print("No se encontraron imágenes en uploads/productos/")
        sys.exit(0)

    print(f"{'DRY RUN — ' if args.dry_run else ''}Procesando {len(images)} imagen(es) en {UPLOADS_DIR}\n")
    print(f"  {'Archivo':40s}  {'Original':>10s}   {'Nuevo':>10s}   Ahorro   Dimensiones")
    print("  " + "-" * 90)

    total_before = total_after = 0
    for path in images:
        before, after = process_image(path, args.dry_run)
        total_before += before
        total_after += after

    print("\n  " + "-" * 90)
    total_savings_pct = (1 - total_after / total_before) * 100 if total_before > 0 else 0
    print(
        f"  {'TOTAL':40s}  {human_size(total_before):>10s} → {human_size(total_after):>10s}  "
        f"(-{total_savings_pct:.0f}%)"
    )
    if args.dry_run:
        print("\n[dry-run] Ningún archivo fue modificado. Ejecuta sin --dry-run para aplicar.")
    else:
        print(f"\nListo. {len(images)} imagen(es) procesada(s).")


if __name__ == "__main__":
    main()
