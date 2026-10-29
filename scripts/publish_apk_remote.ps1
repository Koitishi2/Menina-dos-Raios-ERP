param(
    [Parameter(Mandatory = $true)] [string] $PackageDir,
    [Parameter(Mandatory = $true)] [string] $ReleaseId
)

$ErrorActionPreference = 'Stop'
$hostName = 'root@2.24.124.76'
$remoteRoot = '/opt/menina/backend/static/app-updates'
$remoteStage = "/root/menina_apk_staging/$ReleaseId"
$remoteBackup = "/root/menina_apk_backup_$ReleaseId"
$transcript = Join-Path $env:TEMP ('menina-apk-publish-' + $ReleaseId + '-status.txt')
$metadata = Get-Content -LiteralPath (Join-Path $PackageDir 'latest.json') -Raw | ConvertFrom-Json
$apkName = [string]$metadata.apkFile
$publicBase = 'https://sistema.meninadosraios.com.br/app-updates'

Start-Transcript -Path $transcript -Force | Out-Null
try {
    Write-Host '1/3 Backup remoto e preparo do staging. Digite a senha SSH nesta janela.' -ForegroundColor Cyan
    $backupCommand = 'set -e; d=/opt/menina/backend/static/app-updates; b=' + $remoteBackup + '; s=' + $remoteStage + '; mkdir -p "$b" "$s"; for f in Menina-dos-Raios-Vendas-OFICIAL.apk latest.json catalog.json CHANGELOG-APP.md; do if [ -f "$d/$f" ]; then cp -p "$d/$f" "$b/$f"; fi; done; echo APK_BACKUP_OK=$b; echo APK_STAGE_READY=$s'
    & ssh.exe -o ConnectTimeout=15 -p 22 $hostName $backupCommand
    if ($LASTEXITCODE -ne 0) { throw "Backup/staging SSH falhou (exit $LASTEXITCODE)." }

    Write-Host '2/3 SCP do APK, catálogos, changelog e checksums para staging.' -ForegroundColor Cyan
    $files = @((Join-Path $PackageDir $apkName),(Join-Path $PackageDir 'latest.json'),(Join-Path $PackageDir 'catalog.json'),(Join-Path $PackageDir 'CHANGELOG-APP.md'),(Join-Path $PackageDir 'SHA256SUMS'))
    & scp.exe -P 22 @files "${hostName}:$remoteStage/"
    if ($LASTEXITCODE -ne 0) { throw "SCP para staging falhou (exit $LASTEXITCODE)." }

    Write-Host '3/3 Verificação remota de checksums e promoção.' -ForegroundColor Cyan
    $publishCommand = 'set -e; s=' + $remoteStage + '; d=' + $remoteRoot + '; cd "$s"; sha256sum -c SHA256SUMS; install -d "$d"; for f in Menina-dos-Raios-Vendas-OFICIAL.apk CHANGELOG-APP.md catalog.json; do install -m 0644 "$f" "$d/$f.new"; mv -f "$d/$f.new" "$d/$f"; done; install -m 0644 latest.json "$d/latest.json.new"; mv -f "$d/latest.json.new" "$d/latest.json"; (cd "$d" && sha256sum -c "$s/SHA256SUMS"); echo APK_PUBLISH_OK; cat "$d/latest.json"'
    & ssh.exe -o ConnectTimeout=15 -p 22 $hostName $publishCommand
    if ($LASTEXITCODE -ne 0) { throw "Checksum remoto/promoção falhou (exit $LASTEXITCODE)." }

    Write-Host 'Validando metadados públicos e GET do APK.' -ForegroundColor Cyan
    $expected = Get-Content -LiteralPath (Join-Path $PackageDir 'latest.json') -Raw | ConvertFrom-Json
    $publicMeta = Invoke-RestMethod -Uri "$publicBase/latest.json?release=$ReleaseId" -TimeoutSec 30
    if ($publicMeta.versionName -ne $expected.versionName -or [int]$publicMeta.versionCode -ne [int]$expected.versionCode -or $publicMeta.sha256 -ne $expected.sha256 -or [long]$publicMeta.sizeBytes -ne [long]$expected.sizeBytes) {
        throw 'Metadados públicos divergem do APK promovido.'
    }
    $downloadPath = Join-Path $env:TEMP ('menina-apk-public-' + $ReleaseId + '.apk')
    Invoke-WebRequest -Uri "$publicBase/$apkName?release=$ReleaseId" -OutFile $downloadPath -UseBasicParsing -TimeoutSec 60
    $hash = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($downloadPath)
    try { $downloadHash = ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $hash.Dispose() }
    if ((Get-Item -LiteralPath $downloadPath).Length -ne [long]$expected.sizeBytes -or $downloadHash -ne $expected.sha256) {
        throw 'GET público diverge em tamanho ou SHA-256.'
    }
    Write-Host ("APK_PUBLISH_OK version={0} code={1} size={2} sha256={3} PUBLIC_GET=OK" -f $expected.versionName,$expected.versionCode,$expected.sizeBytes,$expected.sha256) -ForegroundColor Green
    Write-Host "BACKUP_REMOTO=$remoteBackup"
    Write-Host "PUBLICACAO_REMOTA=OK versao=$($expected.versionName) sha256_validado=sim"
}
catch {
    Write-Host "PUBLICACAO=FALHOU $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Write-Host "Log: $transcript"
    Stop-Transcript | Out-Null
    Read-Host 'Pressione Enter para fechar esta janela'
}
