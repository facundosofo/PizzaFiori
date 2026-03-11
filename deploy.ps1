# deploy.ps1 — Construye y despliega el entregable completo (backend + frontend)
# Uso: .\deploy.ps1
# Uso con ruta personalizada: .\deploy.ps1 -Destino "D:\PizzaFiori"
#
# Pasos:
#   1. Detener servicio
#   2. Limpiar __pycache__ de alembic/versions  (evita empaquetar .pyc viejos)
#   3. Build frontend   → npm run build
#   4. Build backend    → pyinstaller pizzafiori.spec --noconfirm
#   5. Copiar artefactos al destino
#   6. Iniciar servicio

param(
    [string]$Destino = "C:\Users\Facundo\Desktop\EntregablePF"
)

$ErrorActionPreference = "Stop"

$RepoRoot    = $PSScriptRoot
$BackendDir  = "$RepoRoot\backend"
$FrontendDir = "$RepoRoot\frontend"

$ExeOrigen   = "$BackendDir\dist\pizzafiori.exe"
$DistOrigen  = "$FrontendDir\dist"
$ExeDestino  = "$Destino\backend\dist\pizzafiori.exe"
$DistDestino = "$Destino\frontend\dist"

# --- Validar destino ---
if (-not (Test-Path $Destino)) {
    Write-Error "La carpeta destino no existe: $Destino"
    exit 1
}

# --- [1/6] Detener servicio ---
Write-Host "`n[1/6] Deteniendo servicio PizzaFiori..." -ForegroundColor Cyan
$svc = Get-Service -Name "PizzaFiori" -ErrorAction SilentlyContinue
if ($svc) {
    Stop-Service -Name "PizzaFiori" -Force
    Start-Sleep -Seconds 2
    Write-Host "      Servicio detenido." -ForegroundColor Green
} else {
    Write-Host "      Servicio no encontrado, continuando..." -ForegroundColor Yellow
}

# --- [2/6] Limpiar __pycache__ de alembic ---
Write-Host "`n[2/6] Limpiando cache de migraciones..." -ForegroundColor Cyan
$alembicCache = "$BackendDir\alembic\versions\__pycache__"
if (Test-Path $alembicCache) {
    Remove-Item -Path $alembicCache -Recurse -Force
    Write-Host "      $alembicCache eliminado." -ForegroundColor Green
} else {
    Write-Host "      Nada que limpiar." -ForegroundColor DarkGray
}

# --- [3/6] Build frontend ---
Write-Host "`n[3/6] Construyendo frontend..." -ForegroundColor Cyan
Push-Location $FrontendDir
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build fallo (exit code $LASTEXITCODE)" }
    Write-Host "      Frontend OK." -ForegroundColor Green
} finally {
    Pop-Location
}

# --- [4/6] Build backend ---
Write-Host "`n[4/6] Construyendo backend (PyInstaller)..." -ForegroundColor Cyan
Push-Location $BackendDir
try {
    # Activar venv si existe (asegura usar la version correcta de pyinstaller)
    $venvActivate = "$BackendDir\.venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) { & $venvActivate }

    pyinstaller pizzafiori.spec --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "pyinstaller fallo (exit code $LASTEXITCODE)" }
    Write-Host "      Backend OK." -ForegroundColor Green
} finally {
    Pop-Location
}

# --- [5/6] Copiar artefactos ---
Write-Host "`n[5/6] Copiando artefactos al destino..." -ForegroundColor Cyan

New-Item -ItemType Directory -Path (Split-Path $ExeDestino) -Force | Out-Null
Copy-Item -Path $ExeOrigen -Destination $ExeDestino -Force
Write-Host "      EXE copiado." -ForegroundColor Green

# Borrar dist viejo para evitar archivos con hashes viejos que queden huerfanos
if (Test-Path $DistDestino) {
    Remove-Item -Path $DistDestino -Recurse -Force
}
Copy-Item -Path $DistOrigen -Destination $DistDestino -Recurse -Force
Write-Host "      Frontend copiado." -ForegroundColor Green

# --- [6/6] Iniciar servicio ---
Write-Host "`n[6/6] Iniciando servicio PizzaFiori..." -ForegroundColor Cyan
if ($svc) {
    Start-Service -Name "PizzaFiori"
    Start-Sleep -Seconds 2
    $estado = (Get-Service -Name "PizzaFiori").Status
    if ($estado -eq "Running") {
        Write-Host "      Servicio iniciado correctamente." -ForegroundColor Green
    } else {
        Write-Host "      El servicio no arranco (estado: $estado). Revisa los logs." -ForegroundColor Red
    }
} else {
    Write-Host "      No hay servicio configurado. Inicia la app manualmente." -ForegroundColor Yellow
}

Write-Host "`n Deploy completado exitosamente.`n" -ForegroundColor Green
