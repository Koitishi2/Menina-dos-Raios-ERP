param(
    [Parameter(Mandatory = $true)] [string] $ProjectRoot,
    [switch] $ValidateOnly
)

$ErrorActionPreference = 'Stop'
trap {
    Write-Host "PREPARACAO_APK=FALHOU $($_.Exception.Message)" -ForegroundColor Red
    Read-Host 'Pressione Enter para fechar esta janela'
    break
}
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$metadataPath = Join-Path $ProjectRoot 'backend\static\app-updates\latest.json'
$catalogPath = Join-Path $ProjectRoot 'backend\static\app-updates\catalog.json'
$changelogPath = Join-Path $ProjectRoot 'backend\static\app-updates\CHANGELOG-APP.md'
$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
$catalog = Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json

foreach ($field in @('versionName', 'versionCode', 'packageName', 'sha256', 'sizeBytes', 'apkFile', 'apkUrl')) {
    if ([string]$metadata.$field -ne [string]$catalog.$field) { throw "latest.json e catalog.json divergem no campo $field." }
}
if ($metadata.packageName -ne 'br.com.meninadosraios.vendas') { throw 'O packageName do catálogo não é o APK oficial.' }
if ($metadata.apkFile -ne 'Menina-dos-Raios-Vendas-OFICIAL.apk') { throw 'O catálogo não aponta para o APK oficial direto.' }
if (-not (Select-String -LiteralPath $changelogPath -Pattern ('Versao estavel atual: `' + [regex]::Escape($metadata.versionName) + '`\.') -Quiet)) {
    throw 'A versão atual do changelog não corresponde ao catálogo.'
}

$sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$buildTools = Get-ChildItem -LiteralPath (Join-Path $sdk 'build-tools') -Directory | Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
if (-not $buildTools) { throw 'Android SDK build-tools não encontrado.' }
$aapt = Join-Path $buildTools.FullName 'aapt.exe'
$apksigner = Join-Path $buildTools.FullName 'apksigner.bat'
if (-not (Test-Path $aapt) -or -not (Test-Path $apksigner)) { throw 'aapt ou apksigner não encontrado.' }
$javaHome = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr'
if (Test-Path -LiteralPath (Join-Path $javaHome 'bin\java.exe')) {
    $env:JAVA_HOME = $javaHome
    $env:PATH = (Join-Path $javaHome 'bin') + ';' + $env:PATH
}

$candidates = @()
$standardApk = Join-Path $ProjectRoot 'android\app\build\outputs\apk\direct\release\app-direct-release.apk'
if (Test-Path -LiteralPath $standardApk) { $candidates += Get-Item -LiteralPath $standardApk }
$tempReleaseRoots = Get-ChildItem -LiteralPath $env:TEMP -Directory -Filter 'menina-apk-release-*' -ErrorAction SilentlyContinue
foreach ($root in $tempReleaseRoots) {
    $candidate = Join-Path $root.FullName $metadata.apkFile
    if (Test-Path -LiteralPath $candidate) { $candidates += Get-Item -LiteralPath $candidate }
}
if (-not $candidates) { throw 'Não encontrei o APK assinado direct para publicação.' }

$sha = [System.Security.Cryptography.SHA256]::Create()
$apk = $null
$actualHash = $null
foreach ($candidate in ($candidates | Sort-Object LastWriteTime -Descending)) {
    $stream = [System.IO.File]::OpenRead($candidate.FullName)
    try { $candidateHash = ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose() }
    if ($candidateHash -eq $metadata.sha256 -and $candidate.Length -eq [long]$metadata.sizeBytes) {
        $apk = $candidate
        $actualHash = $candidateHash
        break
    }
}
$sha.Dispose()
if (-not $apk) { throw 'Nenhum APK local corresponde ao SHA-256 e tamanho do catálogo.' }

$badging = & $aapt dump badging $apk.FullName 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível ler package/version do APK.' }
if ($badging -notmatch "package: name='br\.com\.meninadosraios\.vendas' versionCode='$([int]$metadata.versionCode)' versionName='$([regex]::Escape([string]$metadata.versionName))'") {
    throw 'O package/version embutido no APK não corresponde ao catálogo.'
}

$oldPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$signatureOutput = & $apksigner verify --print-certs $apk.FullName 2>&1 | Out-String
$signatureExit = $LASTEXITCODE
$ErrorActionPreference = $oldPreference
if ($signatureExit -ne 0) { throw 'A assinatura do APK não foi validada.' }
$certificate = [regex]::Match($signatureOutput, 'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]{64})')
if (-not $certificate.Success -or $certificate.Groups[1].Value.ToLowerInvariant() -ne 'd9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f') {
    throw 'O certificado de assinatura não é o certificado oficial.'
}

Write-Host ("APK_VALIDATED version={0} code={1} size={2} sha256={3}" -f $metadata.versionName, $metadata.versionCode, $apk.Length, $actualHash) -ForegroundColor Green
if ($ValidateOnly) { return }

$releaseId = (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + $metadata.versionName + '_' + $actualHash.Substring(0, 8)
$packageDir = Join-Path $env:TEMP ('menina-apk-release-' + $releaseId)
New-Item -ItemType Directory -Path $packageDir | Out-Null
Copy-Item -LiteralPath $apk.FullName -Destination (Join-Path $packageDir $metadata.apkFile)
Copy-Item -LiteralPath $metadataPath -Destination (Join-Path $packageDir 'latest.json')
Copy-Item -LiteralPath $catalogPath -Destination (Join-Path $packageDir 'catalog.json')
Copy-Item -LiteralPath $changelogPath -Destination (Join-Path $packageDir 'CHANGELOG-APP.md')
Set-Content -LiteralPath (Join-Path $packageDir 'SHA256SUMS') -Value ($actualHash + '  ' + $metadata.apkFile) -Encoding ASCII

$remoteRunner = Join-Path $env:TEMP ('menina-apk-publish-' + $releaseId + '.ps1')
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'scripts\publish_apk_remote.ps1') -Destination $remoteRunner
$powershell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
Start-Process -FilePath $powershell -WindowStyle Normal -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-NoExit', '-File', $remoteRunner,
    '-PackageDir', $packageDir, '-ReleaseId', $releaseId
)
Write-Host "Janela de publicação aberta. O APK foi validado; digite a senha SSH somente nela."
