# pizzafiori.spec
# PyInstaller spec file — builds a single-file Windows executable.
#
# Run from backend/ with the venv active:
#   pyinstaller pizzafiori.spec
#
# Output: dist/pizzafiori.exe

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None


# ---------------------------------------------------------------------------
# Collect all submodules and data for packages that rely on dynamic imports
# ---------------------------------------------------------------------------
def _collect(*packages):
    datas, bins, hidden = [], [], []
    for pkg in packages:
        d, b, h = collect_all(pkg)
        datas += d
        bins += b
        hidden += h
    return datas, bins, hidden


extra_datas, extra_bins, extra_hidden = _collect(
    'uvicorn',
    'fastapi',
    'starlette',
    'dependency_injector',
    'psycopg',
    'pydantic',
    'pydantic_settings',
    'alembic',
    'matplotlib',
)

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=extra_bins,
    datas=extra_datas + [
        ('alembic.ini', '.'),
        ('alembic', 'alembic'),
    ],
    hiddenimports=extra_hidden + [
        # SQLAlchemy async + psycopg3 dialect
        'sqlalchemy.dialects.postgresql',
        'sqlalchemy.dialects.postgresql.psycopg',
        'sqlalchemy.ext.asyncio',
        # Alembic — ejecutado programáticamente desde el lifespan de FastAPI
        'alembic',
        'alembic.config',
        'alembic.command',
        'alembic.runtime.migration',
        'alembic.runtime.environment',
        'alembic.operations',
        'alembic.script',
        'alembic.util',
        # python-dotenv
        'dotenv',
        # seeds — bundled como bytecode para que no sea sobreescrito por archivo externo
        'seeds',
        # App subpackages — dependency-injector wires them dynamically
        'app',
        'app.main',
        'app.containers',
        'app.domain',
        'app.application',
        'app.infrastructure',
        'app.presentation',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude dev/test-only packages to reduce exe size
    excludes=['pytest', 'coverage', 'pip_audit', 'pygal'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pizzafiori',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,         # compress with UPX if available (reduces size ~30%)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,     # show console output — useful for NSSM log capture
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
