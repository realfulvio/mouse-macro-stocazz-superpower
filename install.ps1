# Mouse Macro Stocazz Superpower - avvio da PowerShell (senza exe)
#   irm https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.ps1 | iex
# Scarica la release ufficiale da GitHub, verifica lo SHA-256, la estrae in
# %LOCALAPPDATA% e avvia il pythonw.exe firmato PSF. Nessun exe non firmato,
# nessun file con Mark of the Web, nessuna protezione modificata.
# Usa solo cmdlet base (compatibile con Constrained Language Mode).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Version = '1.0.1'
$Repo    = 'realfulvio/mouse-macro-stocazz-superpower'
$Base    = "https://github.com/$Repo/releases/download/v$Version"
$Zip     = "MouseMacroStocazzSuperpower-Windows-v$Version.zip"
$Package = "MouseMacroStocazzSuperpower-Windows-v$Version"
$Root    = Join-Path $env:LOCALAPPDATA 'MouseMacroStocazzSuperpower\Portable'
$Target  = Join-Path $Root $Package
$Python  = Join-Path $Target 'runtime\pythonw.exe'
$Main    = Join-Path $Target 'app\windows_main.py'

if (-not ((Test-Path $Python) -and (Test-Path $Main))) {
    $Work = Join-Path $env:TEMP ('mmss-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $Work | Out-Null
    try {
        Write-Host "Scarico Mouse Macro v$Version ..."
        Invoke-WebRequest -UseBasicParsing -Uri "$Base/$Zip" -OutFile (Join-Path $Work $Zip)
        Invoke-WebRequest -UseBasicParsing -Uri "$Base/SHA256SUMS-v$Version.txt" -OutFile (Join-Path $Work 'sums.txt')
        $line = Get-Content (Join-Path $Work 'sums.txt') | Where-Object { $_ -match [regex]::Escape($Zip) } | Select-Object -First 1
        if (-not $line) { throw 'Hash non trovato in SHA256SUMS.' }
        $expected = ($line -split '\s+')[0].ToLower()
        $actual = (Get-FileHash -Algorithm SHA256 (Join-Path $Work $Zip)).Hash.ToLower()
        if ($actual -ne $expected) { throw "SHA-256 diverso dall'atteso ($actual). Download scartato." }
        New-Item -ItemType Directory -Path $Root -Force | Out-Null
        Expand-Archive -Path (Join-Path $Work $Zip) -DestinationPath $Root -Force
    } finally {
        Remove-Item -Recurse -Force $Work -ErrorAction SilentlyContinue
    }
}
if (-not ((Test-Path $Python) -and (Test-Path $Main))) { throw 'Installazione incompleta.' }
Write-Host 'Avvio Mouse Macro...'
Start-Process -FilePath $Python -ArgumentList @('-B', "`"$Main`"") -WorkingDirectory $Target
