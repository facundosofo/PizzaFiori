# deploy.ps1 — Copia el EXE y el frontend/dist al servidor del cliente
# Uso: .\deploy.ps1
# Uso con ruta personalizada: .\deploy.ps1 -Destino "D:\PizzaFiori"

param(
    [string]$Destino = "C:\Users\Facundo\Desktop\EntregablePF"
)

$RepoRoot  = $PSScriptRoot
$ExeOrigen = "$RepoRoot\backend\dist\pizzafiori.exe"
$DistOrigen = "$RepoRoot\frontend\dist"

$ExeDestino  = "$Destino\backend\dist\pizzafiori.exe"
$DistDestino = "$Destino\frontend\dist"

# --- Validaciones ---
if (-not (Test-Path $ExeOrigen)) {
    Write-Error "No se encontro el EXE en: $ExeOrigen`nEjecuta primero: pyinstaller pizzafiori.spec --noconfirm"
    exit 1
}
if (-not (Test-Path "$DistOrigen\index.html")) {
    Write-Error "No se encontro el frontend en: $DistOrigen`nEjecuta primero: npm run build"
    exit 1
}
if (-not (Test-Path $Destino)) {
    Write-Error "La carpeta destino no existe: $Destino"
    exit 1
}

# --- Detener servicio ---
Write-Host "`n[1/4] Deteniendo servicio PizzaFiori..." -ForegroundColor Cyan
$svc = Get-Service -Name "PizzaFiori" -ErrorAction SilentlyContinue
if ($svc) {
    Stop-Service -Name "PizzaFiori" -Force
    Start-Sleep -Seconds 2
    Write-Host "      Servicio detenido." -ForegroundColor Green
} else {
    Write-Host "      Servicio no encontrado, continuando..." -ForegroundColor Yellow
}

# --- Copiar EXE ---
Write-Host "`n[2/4] Copiando EXE..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path (Split-Path $ExeDestino) -Force | Out-Null
Copy-Item -Path $ExeOrigen -Destination $ExeDestino -Force
Write-Host "      $ExeOrigen -> $ExeDestino" -ForegroundColor Green

# --- Copiar frontend/dist ---
Write-Host "`n[3/4] Copiando frontend/dist..." -ForegroundColor Cyan
# Borrar el dist viejo para evitar archivos con hashes viejos que queden huerfanos
if (Test-Path $DistDestino) {
    Remove-Item -Path $DistDestino -Recurse -Force
}
Copy-Item -Path $DistOrigen -Destination $DistDestino -Recurse -Force
Write-Host "      $DistOrigen -> $DistDestino" -ForegroundColor Green

# --- Iniciar servicio ---
Write-Host "`n[4/4] Iniciando servicio PizzaFiori..." -ForegroundColor Cyan
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
