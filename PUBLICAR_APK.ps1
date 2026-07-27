$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Menina dos Raios - Publicar APK"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Menina dos Raios - Publicacao de atualizacao do aplicativo"
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

$defaultApk = "C:\Users\adria\OneDrive\Documentos\vendas APK\Menina-dos-Raios-Vendas-v1.0.27-OFICIAL.apk"
$apk = Read-Host "Caminho do APK [$defaultApk]"
if ([string]::IsNullOrWhiteSpace($apk)) { $apk = $defaultApk }
$apk = $apk.Trim('"')
if (-not (Test-Path -LiteralPath $apk -PathType Leaf)) { throw "APK nao encontrado: $apk" }

$buildTools = Get-ChildItem -Path "$env:LOCALAPPDATA\Android\Sdk\build-tools" -Directory |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $buildTools) { throw "Android Build Tools nao encontrado." }
$aapt = Join-Path $buildTools.FullName "aapt.exe"
$apksigner = Join-Path $buildTools.FullName "apksigner.bat"
if (-not (Test-Path -LiteralPath $aapt)) { throw "aapt.exe nao encontrado." }
if (-not (Test-Path -LiteralPath $apksigner)) { throw "apksigner.bat nao encontrado." }

$verifyOutput = (& $apksigner verify --verbose --print-certs $apk 2>&1 | Out-String)
Write-Host $verifyOutput
if ($LASTEXITCODE -ne 0) { throw "A assinatura do APK e invalida." }
$expectedCertificate = "d9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f"
if ($verifyOutput -notmatch $expectedCertificate) {
    throw "Este APK nao foi assinado com a chave oficial da Menina dos Raios. Publicacao bloqueada."
}
$packageLine = (& $aapt dump badging $apk | Select-String -Pattern "^package:" | Select-Object -First 1).Line
if ($packageLine -notmatch "versionCode='([0-9]+)'" -or $packageLine -notmatch "versionName='([^']+)'" ) {
    throw "Nao foi possivel identificar a versao do APK."
}
$versionCode = [int]([regex]::Match($packageLine, "versionCode='([0-9]+)'").Groups[1].Value)
$versionName = [regex]::Match($packageLine, "versionName='([^']+)'").Groups[1].Value
if ($packageLine -notmatch "name='br\.com\.meninadosraios\.vendas'") {
    throw "Identificador incorreto. O APK oficial deve usar br.com.meninadosraios.vendas."
}
if ($versionName -notmatch '^\d+\.\d+\.\d+$') {
    throw "Versao invalida: $versionName. Use o formato 1.0.1, 1.0.2 ... 1.0.999, depois 1.1.0."
}
$versionParts = $versionName.Split('.')
if ([int]$versionParts[2] -gt 999) {
    throw "A revisao nao pode passar de 999. Depois de 1.0.999 use 1.1.0."
}
Write-Host "Versao identificada automaticamente: $versionName (codigo $versionCode)" -ForegroundColor Cyan
$notes = (Read-Host "Novidades desta versao").Trim()
if ([string]::IsNullOrWhiteSpace($notes)) { $notes = "Melhorias e correcoes." }

$updatesDir = Join-Path $PSScriptRoot "backend\static\app-updates"
New-Item -ItemType Directory -Path $updatesDir -Force | Out-Null
$publishedApk = Join-Path $updatesDir "Menina-dos-Raios-Vendas.apk"
$metadata = Join-Path $updatesDir "latest.json"
$changelogSource = Join-Path $PSScriptRoot "CHANGELOG-APP.md"
$changelogPublished = Join-Path $updatesDir "CHANGELOG-APP.md"
Copy-Item -LiteralPath $apk -Destination $publishedApk -Force
$hash = (Get-FileHash -LiteralPath $publishedApk -Algorithm SHA256).Hash.ToLowerInvariant()

[ordered]@{
    versionCode = $versionCode
    versionName = $versionName
    apkUrl = "https://sistema.meninadosraios.com.br/app-updates/Menina-dos-Raios-Vendas.apk"
    sha256 = $hash
    notes = $notes
} | ConvertTo-Json | Set-Content -LiteralPath $metadata -Encoding UTF8

if (-not (Test-Path -LiteralPath $changelogSource)) {
    "# Changelog - Menina dos Raios Vendas`r`n" | Set-Content -LiteralPath $changelogSource -Encoding UTF8
}
$versionHeading = "## [$versionName]"
if (-not (Select-String -LiteralPath $changelogSource -Pattern ([regex]::Escape($versionHeading)) -Quiet)) {
    $date = Get-Date -Format "dd/MM/yyyy HH:mm"
    Add-Content -LiteralPath $changelogSource -Encoding UTF8 -Value "`r`n## [$versionName] - $date`r`n`r`n- $notes`r`n"
}
Copy-Item -LiteralPath $changelogSource -Destination $changelogPublished -Force

Write-Host ""
Write-Host "Enviando APK e catalogo ao servidor..." -ForegroundColor Cyan
& ssh root@2.24.124.76 "mkdir -p /opt/menina/backend/static/app-updates"
if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel preparar a pasta no servidor." }
& scp $publishedApk root@2.24.124.76:/opt/menina/backend/static/app-updates/Menina-dos-Raios-Vendas.apk
if ($LASTEXITCODE -ne 0) { throw "Falha ao enviar o APK." }
& scp $metadata root@2.24.124.76:/opt/menina/backend/static/app-updates/latest.json
if ($LASTEXITCODE -ne 0) { throw "Falha ao enviar o catalogo." }
& scp $changelogPublished root@2.24.124.76:/opt/menina/backend/static/app-updates/CHANGELOG-APP.md
if ($LASTEXITCODE -ne 0) { throw "Falha ao enviar o changelog." }

Write-Host ""
Write-Host "Atualizacao $versionName publicada com sucesso." -ForegroundColor Green
Write-Host "Catalogo: https://sistema.meninadosraios.com.br/app-updates/latest.json"
Write-Host "APK: https://sistema.meninadosraios.com.br/app-updates/Menina-dos-Raios-Vendas.apk"
Write-Host "Changelog: https://sistema.meninadosraios.com.br/app-updates/CHANGELOG-APP.md"
