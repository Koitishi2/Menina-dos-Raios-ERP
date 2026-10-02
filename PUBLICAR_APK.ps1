param(
    [string]$Notes = "",
    [switch]$DryRun,
    [string]$SourceApkPath = "",
    [string]$AppUpdatesDirectory = ""
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Menina dos Raios - Publicar APK"

$root = $PSScriptRoot
$OFFICIAL_APK_NAME = "Menina-dos-Raios-Vendas-OFICIAL.apk"
$LATEST_JSON_NAME = "latest.json"
$CATALOG_JSON_NAME = "catalog.json"
$CHANGELOG_NAME = "CHANGELOG-APP.md"
$EXPECTED_PACKAGE = "br.com.meninadosraios.vendas"
$DEFAULT_APK_BASE_URL = "https://sistema.meninadosraios.com.br/app-updates"
$script:PublishStage = "START"
$logDir = Join-Path $root "logs_apk_publicacao"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logPath = Join-Path $logDir ("apk_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
trap {
    $message = $_.Exception.Message
    Write-Host "ERRO [$script:PublishStage]: $message" -ForegroundColor Red
    Write-Host "Log: $logPath" -ForegroundColor Yellow
    try { Stop-Transcript | Out-Null } catch {}
    exit 1
}
Start-Transcript -Path $logPath -Force | Out-Null

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
    param([hashtable]$Config, [string]$Name)
    if (-not $Config.ContainsKey($Name) -or [string]::IsNullOrWhiteSpace($Config[$Name]) -or $Config[$Name] -match "CONFIGURAR") {
        throw "Configuracao obrigatoria ausente: $Name"
    }
    return $Config[$Name]
}

function Invoke-Checked {
    param([string]$FilePath, [string[]]$ArgumentList, [string]$ErrorMessage)
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) { throw $ErrorMessage }
}

function Assert-SafeRemotePath {
    param([string]$Name, [string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match "CONFIGURAR") {
        throw "Caminho remoto obrigatorio ausente: $Name"
    }
    if ($Value -notmatch '^/' -or $Value -eq "/" -or $Value -match "['`"\^]" -or $Value -match '\\') {
        throw "Caminho remoto inseguro em $Name."
    }
}

function Get-BuildTool {
    param([string]$ToolName)
    $root = Join-Path $env:LOCALAPPDATA "Android\Sdk\build-tools"
    $dir = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if (-not $dir) { return "" }
    $path = Join-Path $dir.FullName $ToolName
    if (Test-Path -LiteralPath $path -PathType Leaf) { return $path }
    return ""
}

function Read-ApkInfo {
    param([string]$Apk)
    $info = [ordered]@{
        versionName = "desconhecida"
        versionCode = 0
        packageName = "desconhecido"
        extracted = $false
        warning = ""
    }
    $aapt = Get-BuildTool "aapt.exe"
    if ([string]::IsNullOrWhiteSpace($aapt)) {
        $info.warning = "aapt.exe nao encontrado. Versao/pacote ficarao como fallback."
        return $info
    }
    try {
        $line = (& $aapt dump badging $Apk | Select-String -Pattern "^package:" | Select-Object -First 1).Line
        if ($line -match "name='([^']+)'") { $info.packageName = $matches[1] }
        if ($line -match "versionName='([^']+)'") { $info.versionName = $matches[1] }
        if ($line -match "versionCode='([0-9]+)'") { $info.versionCode = [int]$matches[1] }
        $info.extracted = ($info.versionCode -gt 0 -and $info.versionName -ne "desconhecida" -and $info.packageName -ne "desconhecido")
        if (-not $info.extracted) { $info.warning = "Nao foi possivel extrair todos os dados do APK. Usando fallback parcial." }
    } catch {
        $info.warning = "Falha ao ler APK com aapt: $($_.Exception.Message). Usando fallback."
    }
    return $info
}

function Test-ApkSignature {
    param([string]$Apk)
    $apksigner = Get-BuildTool "apksigner.bat"
    if ([string]::IsNullOrWhiteSpace($apksigner)) {
        Write-Host "AVISO: apksigner.bat nao encontrado. Assinatura nao foi validada pelo script." -ForegroundColor Yellow
        return
    }
    $verifyOutput = (& $apksigner verify --verbose $Apk 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) {
        throw "A assinatura do APK e invalida. Publicacao bloqueada."
    }
    Write-Host "Assinatura do APK: OK" -ForegroundColor Green
}

function New-CatalogObject {
    param(
        [System.Collections.IDictionary]$ApkInfo,
        [string]$Hash,
        [string]$ReleaseNotes,
        [string]$BaseUrl,
        [long]$SizeBytes
    )
    $publishedAt = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    return [ordered]@{
        versionName = $ApkInfo.versionName
        versionCode = $ApkInfo.versionCode
        packageName = $ApkInfo.packageName
        sha256 = $Hash
        releaseNotes = $ReleaseNotes
        notes = $ReleaseNotes
        apkFile = $OFFICIAL_APK_NAME
        apkUrl = "$BaseUrl/$OFFICIAL_APK_NAME"
        sizeBytes = $SizeBytes
        publishedAt = $publishedAt
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Menina dos Raios - Publicacao otimizada do APK"
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

$script:PublishStage = "CONFIG"
$config = Read-BatchConfig (Join-Path $root "atualizarrefatorado.local.bat")
$APK_PATH = $SourceApkPath
if ([string]::IsNullOrWhiteSpace($APK_PATH) -and $config.ContainsKey("APK_SOURCE_PATH")) {
    $APK_PATH = [string]$config["APK_SOURCE_PATH"]
}
if ([string]::IsNullOrWhiteSpace($APK_PATH)) {
    $APK_PATH = Join-Path $root "backend\static\app-updates\$OFFICIAL_APK_NAME"
}
$APP_UPDATES_DIR = $AppUpdatesDirectory
if ([string]::IsNullOrWhiteSpace($APP_UPDATES_DIR) -and $config.ContainsKey("APP_UPDATES_DIR")) {
    $APP_UPDATES_DIR = [string]$config["APP_UPDATES_DIR"]
}
if ([string]::IsNullOrWhiteSpace($APP_UPDATES_DIR)) {
    $APP_UPDATES_DIR = Join-Path $root "backend\static\app-updates"
}
if (-not (Test-Path -LiteralPath $APK_PATH -PathType Leaf)) {
    throw "APK oficial nao encontrado em $APK_PATH. Configure APK_SOURCE_PATH localmente ou use -SourceApkPath."
}
$hostName = Require-ConfigValue $config "HOST"
$port = Require-ConfigValue $config "PORT"
$user = Require-ConfigValue $config "USER"
$remoteStaticDir = Require-ConfigValue $config "REMOTE_STATIC_DIR"
$remoteBackupDir = Require-ConfigValue $config "REMOTE_BACKUP_DIR"
Assert-SafeRemotePath "REMOTE_STATIC_DIR" $remoteStaticDir
Assert-SafeRemotePath "REMOTE_BACKUP_DIR" $remoteBackupDir

$apkBaseUrl = $DEFAULT_APK_BASE_URL
if ($config.ContainsKey("APK_PUBLIC_BASE_URL") -and -not [string]::IsNullOrWhiteSpace($config["APK_PUBLIC_BASE_URL"])) {
    $apkBaseUrl = ($config["APK_PUBLIC_BASE_URL"] -as [string]).TrimEnd("/")
}

$script:PublishStage = "APK-INSPECT"
$apkInfo = Read-ApkInfo $APK_PATH
if (-not [string]::IsNullOrWhiteSpace($apkInfo.warning)) {
    Write-Host "AVISO: $($apkInfo.warning)" -ForegroundColor Yellow
}
if ($apkInfo.packageName -ne "desconhecido" -and $apkInfo.packageName -ne $EXPECTED_PACKAGE) {
    throw "Package incorreto: $($apkInfo.packageName). Esperado: $EXPECTED_PACKAGE"
}

$script:PublishStage = "SIGNATURE"
Test-ApkSignature $APK_PATH

$hash = (Get-FileHash -LiteralPath $APK_PATH -Algorithm SHA256).Hash.ToLowerInvariant()
$size = (Get-Item -LiteralPath $APK_PATH).Length
if (-not $apkInfo.extracted) {
    $existingLatestPath = Join-Path $APP_UPDATES_DIR $LATEST_JSON_NAME
    if (Test-Path -LiteralPath $existingLatestPath -PathType Leaf) {
        try {
            $existingLatest = Get-Content -LiteralPath $existingLatestPath -Raw | ConvertFrom-Json
            if ($existingLatest.sha256 -and $existingLatest.sha256.ToLowerInvariant() -eq $hash -and
                $existingLatest.versionCode -gt 0 -and $existingLatest.packageName) {
                $apkInfo.versionName = [string]$existingLatest.versionName
                $apkInfo.versionCode = [int]$existingLatest.versionCode
                $apkInfo.packageName = [string]$existingLatest.packageName
                $apkInfo.extracted = $true
                $apkInfo.warning = "Metadados reutilizados do catalogo porque o hash do APK e identico."
            }
        } catch {
            $apkInfo.warning = "Catalogo local indisponivel para fallback de metadados."
        }
    }
    if (-not $apkInfo.extracted) {
        throw "Nao foi possivel identificar os metadados deste APK. Instale o Android build-tools ou selecione um APK cujo hash corresponda ao catalogo local."
    }
}

Write-Host "APK selecionado : $APK_PATH"
Write-Host "Pacote          : $($apkInfo.packageName)"
Write-Host "VersionName     : $($apkInfo.versionName)"
Write-Host "VersionCode     : $($apkInfo.versionCode)"
Write-Host "SHA-256         : $hash"
Write-Host "Tamanho         : $size bytes"
Write-Host ""

$script:PublishStage = "CONFIRM"
$confirm = Read-Host "Deseja publicar este APK? (S/N)"
if ($confirm -notmatch '^[sS]$') {
    Write-Host "Publicacao cancelada pelo operador." -ForegroundColor Yellow
    Stop-Transcript | Out-Null
    exit 2
}

if ([string]::IsNullOrWhiteSpace($Notes)) {
    $Notes = (Read-Host "Descricao/novidades da versao (opcional)").Trim()
}
if ([string]::IsNullOrWhiteSpace($Notes)) { $Notes = "Melhorias e correcoes." }

$script:PublishStage = "LOCAL-METADATA"
New-Item -ItemType Directory -Path $APP_UPDATES_DIR -Force | Out-Null
$localApk = Join-Path $APP_UPDATES_DIR $OFFICIAL_APK_NAME
$latestJson = Join-Path $APP_UPDATES_DIR $LATEST_JSON_NAME
$catalogJson = Join-Path $APP_UPDATES_DIR $CATALOG_JSON_NAME
$changelog = Join-Path $APP_UPDATES_DIR $CHANGELOG_NAME

if ([IO.Path]::GetFullPath($APK_PATH) -ne [IO.Path]::GetFullPath($localApk)) {
    Copy-Item -LiteralPath $APK_PATH -Destination $localApk -Force
}
$catalog = New-CatalogObject -ApkInfo $apkInfo -Hash $hash -ReleaseNotes $Notes -BaseUrl $apkBaseUrl -SizeBytes $size
$catalogJsonText = $catalog | ConvertTo-Json
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($catalogJson, $catalogJsonText + "`r`n", $utf8NoBom)
[System.IO.File]::WriteAllText($latestJson, $catalogJsonText + "`r`n", $utf8NoBom)

if (-not (Test-Path -LiteralPath $changelog -PathType Leaf)) {
    "# Changelog - Menina dos Raios Vendas`r`n" | Set-Content -LiteralPath $changelog -Encoding UTF8
}
$versionHeading = "## [$($apkInfo.versionName)]"
if ($apkInfo.versionName -ne "desconhecida" -and -not (Select-String -LiteralPath $changelog -Pattern ([regex]::Escape($versionHeading)) -Quiet)) {
    $date = Get-Date -Format "dd/MM/yyyy HH:mm"
    Add-Content -LiteralPath $changelog -Encoding UTF8 -Value "`r`n## [$($apkInfo.versionName)] - $date`r`n`r`n- $Notes`r`n"
}

Write-Host ""
Write-Host "Catalogos locais atualizados:" -ForegroundColor Cyan
Write-Host " - $latestJson"
Write-Host " - $catalogJson"
Write-Host "APK local oficial:"
Write-Host " - $localApk"

if ($DryRun) {
    Write-Host ""
    Write-Host "DRY_RUN solicitado. Nenhum SSH/SCP sera executado." -ForegroundColor Yellow
    Write-Host "Log: $logPath"
    Stop-Transcript | Out-Null
    exit 0
}

$remoteAppUpdatesDir = "$remoteStaticDir/app-updates"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$remoteApkBackupDir = "$remoteBackupDir/apk-publications/$timestamp"

Write-Host ""
Write-Host "Enviando para o servidor. A senha sera pedida pelo SSH/SCP." -ForegroundColor Cyan
Write-Host "Destino: $remoteAppUpdatesDir"

$script:PublishStage = "REMOTE-BACKUP"
$backupCommand = "set -e; mkdir -p '$remoteAppUpdatesDir' '$remoteApkBackupDir'; find '$remoteAppUpdatesDir' -maxdepth 1 -type f \( -name '*.apk' -o -name 'latest.json' -o -name 'catalog.json' -o -name 'CHANGELOG-APP.md' \) -exec cp -p {} '$remoteApkBackupDir/' \;; echo APK_BACKUP_OK"
Invoke-Checked "ssh" @("-p", $port, "$user@$hostName", $backupCommand) "Falha ao preparar backup remoto."

$script:PublishStage = "REMOTE-UPLOAD"

Invoke-Checked "scp" @("-P", $port, $localApk, "$user@$hostName`:$remoteAppUpdatesDir/$OFFICIAL_APK_NAME") "Falha ao enviar APK oficial."
Invoke-Checked "scp" @("-P", $port, $latestJson, "$user@$hostName`:$remoteAppUpdatesDir/$LATEST_JSON_NAME") "Falha ao enviar latest.json."
Invoke-Checked "scp" @("-P", $port, $catalogJson, "$user@$hostName`:$remoteAppUpdatesDir/$CATALOG_JSON_NAME") "Falha ao enviar catalog.json."
Invoke-Checked "scp" @("-P", $port, $changelog, "$user@$hostName`:$remoteAppUpdatesDir/$CHANGELOG_NAME") "Falha ao enviar changelog."

$script:PublishStage = "REMOTE-VALIDATE"
$remoteHashLine = "$hash  $remoteAppUpdatesDir/$OFFICIAL_APK_NAME"
$validateCommand = "set -e; test -f '$remoteAppUpdatesDir/$OFFICIAL_APK_NAME'; test -f '$remoteAppUpdatesDir/$LATEST_JSON_NAME'; test -f '$remoteAppUpdatesDir/$CATALOG_JSON_NAME'; printf '%s\n' '$remoteHashLine' | sha256sum -c -; grep -Eq '""sha256""[[:space:]]*:[[:space:]]*""$hash""' '$remoteAppUpdatesDir/$LATEST_JSON_NAME'; grep -Eq '""versionCode""[[:space:]]*:[[:space:]]*$($apkInfo.versionCode)' '$remoteAppUpdatesDir/$LATEST_JSON_NAME'; echo APK_PUBLICATION_OK"
Invoke-Checked "ssh" @("-p", $port, "$user@$hostName", $validateCommand) "Falha ao validar arquivos publicados."

Write-Host ""
Write-Host "APK publicado com sucesso." -ForegroundColor Green
Write-Host "VersionName: $($apkInfo.versionName)"
Write-Host "VersionCode: $($apkInfo.versionCode)"
Write-Host "SHA-256: $hash"
Write-Host "URL: $apkBaseUrl/$OFFICIAL_APK_NAME"
Write-Host "Log: $logPath"
$script:PublishStage = "COMPLETE"
Stop-Transcript | Out-Null
