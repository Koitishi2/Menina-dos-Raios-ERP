param(
    [string]$ApkPath = "",
    [string]$Notes = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Menina dos Raios - Publicar APK"

function Read-BatchConfig {
    param([string]$Path)
    $config = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Configuracao local nao encontrada: atualizarrefatorado.local.bat"
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^\s*set\s+"([^=]+)=(.*)"\s*$') {
            $config[$matches[1]] = $matches[2]
        }
    }
    return $config
}

function Require-ConfigValue {
    param(
        [hashtable]$Config,
        [string]$Name
    )
    if (-not $Config.ContainsKey($Name) -or [string]::IsNullOrWhiteSpace($Config[$Name]) -or $Config[$Name] -match "CONFIGURAR") {
        throw "Configuracao obrigatoria ausente: $Name"
    }
    return $Config[$Name]
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$ErrorMessage
    )
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw $ErrorMessage
    }
}

function Assert-SafeRemoteCommand {
    param([string]$Command)
    $blocked = @(
        '\^',
        '\\x5e',
        '\brestart\b',
        '\bstop\b',
        '\bstart\b',
        '\breboot\b',
        '\bshutdown\b',
        'rm\s+-rf',
        'ATUALIZAR\.bat'
    )
    foreach ($pattern in $blocked) {
        if ($Command -match $pattern) {
            throw "Comando remoto bloqueado por seguranca."
        }
    }
}

function Assert-SafeRemotePath {
    param(
        [string]$Name,
        [string]$Value
    )
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match "CONFIGURAR") {
        throw "Caminho remoto obrigatorio ausente: $Name"
    }
    if ($Value -notmatch '^/' -or $Value -eq "/" -or $Value -match "['`"\^]" -or $Value -match '\\') {
        throw "Caminho remoto inseguro em $Name."
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Menina dos Raios - Publicacao segura do APK"
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

$root = $PSScriptRoot
$config = Read-BatchConfig (Join-Path $root "atualizarrefatorado.local.bat")
$hostName = Require-ConfigValue $config "HOST"
$port = Require-ConfigValue $config "PORT"
$user = Require-ConfigValue $config "USER"
$remoteStaticDir = Require-ConfigValue $config "REMOTE_STATIC_DIR"
$remoteBackupDir = Require-ConfigValue $config "REMOTE_BACKUP_DIR"
Assert-SafeRemotePath "REMOTE_STATIC_DIR" $remoteStaticDir
Assert-SafeRemotePath "REMOTE_BACKUP_DIR" $remoteBackupDir
if ($remoteBackupDir -like "$remoteStaticDir*") {
    throw "REMOTE_BACKUP_DIR deve ficar fora da pasta static/app-updates."
}
$apkPublicBaseUrl = ""
if ($config.ContainsKey("APK_PUBLIC_BASE_URL")) {
    $apkPublicBaseUrl = ($config["APK_PUBLIC_BASE_URL"] -as [string]).TrimEnd("/")
}

if ([string]::IsNullOrWhiteSpace($ApkPath)) {
    $ApkPath = Read-Host "Caminho do APK release assinado"
}
$apk = $ApkPath.Trim('"')
if (-not (Test-Path -LiteralPath $apk -PathType Leaf)) {
    throw "APK nao encontrado: $apk"
}
if ([IO.Path]::GetExtension($apk).ToLowerInvariant() -ne ".apk") {
    throw "Arquivo informado nao e APK: $apk"
}

$buildToolsRoot = Join-Path $env:LOCALAPPDATA "Android\Sdk\build-tools"
$buildTools = Get-ChildItem -Path $buildToolsRoot -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $buildTools) { throw "Android Build Tools nao encontrado em ambiente local." }
$aapt = Join-Path $buildTools.FullName "aapt.exe"
$apksigner = Join-Path $buildTools.FullName "apksigner.bat"
if (-not (Test-Path -LiteralPath $aapt)) { throw "aapt.exe nao encontrado." }
if (-not (Test-Path -LiteralPath $apksigner)) { throw "apksigner.bat nao encontrado." }

$verifyOutput = (& $apksigner verify --verbose --print-certs $apk 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw "A assinatura do APK e invalida." }
$expectedCertificate = "d9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f"
if ($verifyOutput -notmatch $expectedCertificate) {
    throw "Este APK nao foi assinado com a chave oficial esperada. Publicacao bloqueada."
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
    throw "Versao invalida: $versionName. Use formato semver, por exemplo 2.0.1."
}
if ([string]::IsNullOrWhiteSpace($Notes)) {
    $Notes = (Read-Host "Novidades desta versao").Trim()
}
if ([string]::IsNullOrWhiteSpace($Notes)) { $Notes = "Melhorias e correcoes." }

$updatesDir = Join-Path $root "backend\static\app-updates"
New-Item -ItemType Directory -Path $updatesDir -Force | Out-Null
$publishedFileName = "menina-$versionName.apk"
$publishedApk = Join-Path $updatesDir $publishedFileName
$metadata = Join-Path $updatesDir "latest.json"
$changelogPublished = Join-Path $updatesDir "CHANGELOG-APP.md"

Copy-Item -LiteralPath $apk -Destination $publishedApk -Force
$hash = (Get-FileHash -LiteralPath $publishedApk -Algorithm SHA256).Hash.ToLowerInvariant()
$size = (Get-Item -LiteralPath $publishedApk).Length

$apkUrl = $publishedFileName
if (-not [string]::IsNullOrWhiteSpace($apkPublicBaseUrl)) {
    $apkUrl = "$apkPublicBaseUrl/$publishedFileName"
}

[ordered]@{
    versionCode = $versionCode
    versionName = $versionName
    apkFile = $publishedFileName
    apkUrl = $apkUrl
    sha256 = $hash
    sizeBytes = $size
    generatedAt = (Get-Date).ToString("s")
    notes = $Notes
} | ConvertTo-Json | Set-Content -LiteralPath $metadata -Encoding UTF8

if (-not (Test-Path -LiteralPath $changelogPublished)) {
    "# Changelog - Menina dos Raios Vendas`r`n" | Set-Content -LiteralPath $changelogPublished -Encoding UTF8
}
$versionHeading = "## [$versionName]"
if (-not (Select-String -LiteralPath $changelogPublished -Pattern ([regex]::Escape($versionHeading)) -Quiet)) {
    $date = Get-Date -Format "dd/MM/yyyy HH:mm"
    Add-Content -LiteralPath $changelogPublished -Encoding UTF8 -Value "`r`n## [$versionName] - $date`r`n`r`n- $Notes`r`n"
}

$remoteAppUpdatesDir = "$remoteStaticDir/app-updates"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$remoteApkBackupDir = "$remoteBackupDir/apk-publications/$timestamp"
$localLogDir = Join-Path $root "logs_apk_publicacao"
New-Item -ItemType Directory -Path $localLogDir -Force | Out-Null
$logFile = Join-Path $localLogDir "PUBLICAR_APK_$timestamp.log"

Write-Host ""
Write-Host "Versao APK: $versionName (versionCode $versionCode)" -ForegroundColor Cyan
Write-Host "Arquivo local preparado: backend/static/app-updates/$publishedFileName"
Write-Host "Manifesto local: backend/static/app-updates/latest.json"
Write-Host "SHA-256: $hash"
Write-Host "Tamanho: $size bytes"
Write-Host "Destino remoto: [REMOTE_STATIC_DIR]/app-updates"
Write-Host "Backup remoto previo: [REMOTE_BACKUP_DIR]/apk-publications/$timestamp"
Write-Host "Backend, banco, .env, uploads, logs e auth_info_baileys nao serao tocados."
Write-Host "Servico menina nao sera reiniciado."
Write-Host ""

@(
    "version=$versionName",
    "versionCode=$versionCode",
    "file=$publishedFileName",
    "sha256=$hash",
    "sizeBytes=$size",
    "remoteDir=[REMOTE_STATIC_DIR]/app-updates",
    "backupDir=[REMOTE_BACKUP_DIR]/apk-publications/$timestamp"
) | Set-Content -LiteralPath $logFile -Encoding UTF8

if ($DryRun) {
    Write-Host "DRY_RUN solicitado. Nenhum SSH/SCP sera executado." -ForegroundColor Yellow
    exit 0
}

$confirm = Read-Host "Confirmar envio remoto do APK e manifesto? [S/N]"
if ($confirm -notmatch '^[sS]$') {
    Write-Host "Publicacao cancelada pelo operador." -ForegroundColor Yellow
    exit 2
}

$remoteBackupCommand = "set -e; mkdir -p '$remoteAppUpdatesDir' '$remoteApkBackupDir'; find '$remoteAppUpdatesDir' -maxdepth 1 -type f \( -name '*.apk' -o -name 'latest.json' -o -name 'CHANGELOG-APP.md' \) -exec cp -p {} '$remoteApkBackupDir/' \;; echo APK_BACKUP_OK"
Assert-SafeRemoteCommand $remoteBackupCommand
Invoke-Checked "ssh" @("-p", $port, "$user@$hostName", $remoteBackupCommand) "Falha ao criar backup remoto do app-updates."

Invoke-Checked "scp" @("-P", $port, $publishedApk, "$user@$hostName`:$remoteAppUpdatesDir/$publishedFileName") "Falha ao enviar APK."
Invoke-Checked "scp" @("-P", $port, $metadata, "$user@$hostName`:$remoteAppUpdatesDir/latest.json") "Falha ao enviar latest.json."
Invoke-Checked "scp" @("-P", $port, $changelogPublished, "$user@$hostName`:$remoteAppUpdatesDir/CHANGELOG-APP.md") "Falha ao enviar changelog."

$remoteValidateCommand = "set -e; test -f '$remoteAppUpdatesDir/$publishedFileName'; test -f '$remoteAppUpdatesDir/latest.json'; test -f '$remoteAppUpdatesDir/CHANGELOG-APP.md'; echo APK_PUBLICATION_OK"
Assert-SafeRemoteCommand $remoteValidateCommand
Invoke-Checked "ssh" @("-p", $port, "$user@$hostName", $remoteValidateCommand) "Falha ao validar arquivos publicados no servidor."

Write-Host ""
Write-Host "Atualizacao APK $versionName publicada com sucesso." -ForegroundColor Green
Write-Host "Backup remoto criado antes da substituicao."
