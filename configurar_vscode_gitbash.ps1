<#
Configura Git Bash como terminal integrada por defecto en Visual Studio Code.

Uso (desde Git Bash o PowerShell):
    powershell -ExecutionPolicy Bypass -File configurar_vscode_gitbash.ps1

Que hace:
  - Busca bash.exe de Git para Windows en las rutas de instalacion habituales.
  - Edita %APPDATA%\Code\User\settings.json agregando/actualizando:
      "terminal.integrated.defaultProfile.windows": "Git Bash"
      "terminal.integrated.profiles.windows"."Git Bash".path
  - Deja el resto de tu settings.json intacto, y guarda un backup .bak antes
    de tocar nada.
  - Si settings.json tiene comentarios (jsonc) y no se puede parsear
    automaticamente, no lo toca: imprime el fragmento para pegar a mano.
#>

$ErrorActionPreference = "Stop"

$candidatePaths = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files (x86)\Git\bin\bash.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Git\bin\bash.exe")
)
$gitBashPath = $candidatePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $gitBashPath) {
    Write-Host "No se encontro Git Bash instalado (bash.exe) en las rutas habituales." -ForegroundColor Red
    Write-Host "Instala Git para Windows primero: https://git-scm.com/downloads/win" -ForegroundColor Red
    exit 1
}

Write-Host "Git Bash encontrado en: $gitBashPath"

$settingsPath = Join-Path $env:APPDATA "Code\User\settings.json"
$settingsDir = Split-Path $settingsPath

if (-not (Test-Path $settingsDir)) {
    New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
}
if (-not (Test-Path $settingsPath)) {
    Set-Content -Path $settingsPath -Value "{`n}`n" -Encoding utf8
    Write-Host "No existia settings.json de VS Code, se creo uno nuevo vacio."
}

$fragmentObj = [PSCustomObject]@{
    "terminal.integrated.defaultProfile.windows" = "Git Bash"
    "terminal.integrated.profiles.windows"       = [PSCustomObject]@{
        "Git Bash" = [PSCustomObject]@{ path = $gitBashPath }
    }
}
$fragment = $fragmentObj | ConvertTo-Json -Depth 10

try {
    $raw = Get-Content -Path $settingsPath -Raw
    $settings = $raw | ConvertFrom-Json
}
catch {
    Write-Host "No se pudo leer settings.json automaticamente (puede tener comentarios // o comas colgantes)." -ForegroundColor Yellow
    Write-Host "Abre VS Code (Ctrl+, luego el icono de 'Abrir settings.json') y pega esto dentro de las llaves { }:" -ForegroundColor Yellow
    Write-Host $fragment
    exit 1
}

if ($null -eq $settings) {
    $settings = New-Object PSObject
}

if ($settings.PSObject.Properties.Name -notcontains "terminal.integrated.profiles.windows") {
    $settings | Add-Member -NotePropertyName "terminal.integrated.profiles.windows" -NotePropertyValue (New-Object PSObject)
}
$profiles = $settings."terminal.integrated.profiles.windows"

$gitBashProfile = New-Object PSObject -Property @{ path = $gitBashPath }
if ($profiles.PSObject.Properties.Name -contains "Git Bash") {
    $profiles."Git Bash" = $gitBashProfile
}
else {
    $profiles | Add-Member -NotePropertyName "Git Bash" -NotePropertyValue $gitBashProfile
}

if ($settings.PSObject.Properties.Name -contains "terminal.integrated.defaultProfile.windows") {
    $settings."terminal.integrated.defaultProfile.windows" = "Git Bash"
}
else {
    $settings | Add-Member -NotePropertyName "terminal.integrated.defaultProfile.windows" -NotePropertyValue "Git Bash"
}

$backupPath = "$settingsPath.bak"
Copy-Item -Path $settingsPath -Destination $backupPath -Force

$settings | ConvertTo-Json -Depth 10 | Set-Content -Path $settingsPath -Encoding utf8

Write-Host ""
Write-Host "Listo. Git Bash quedo como terminal por defecto en VS Code." -ForegroundColor Green
Write-Host "Backup del settings.json anterior en: $backupPath"
Write-Host "Reinicia VS Code (o abre una terminal nueva desde el menu Terminal > New Terminal) para que tome el cambio."
