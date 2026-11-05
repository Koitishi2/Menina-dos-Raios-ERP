param(
    [Parameter(Mandatory = $true)] [string] $ProjectRoot,
    [switch] $ValidateOnly,
    [switch] $CheckOnly
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$transcript = Join-Path $env:TEMP ('menina-apk-prepare-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '-status.txt')
Start-Transcript -Path $transcript -Force | Out-Null

function Get-AndroidSourceFingerprint([string] $Root) {
    $androidRoot = Join-Path $Root 'android'
    $paths = @('app/src/main','app/build.gradle','build.gradle','settings.gradle','gradle.properties','gradle/libs.versions.toml')
    $files = @()
    foreach ($relative in $paths) {
        $path = Join-Path $androidRoot $relative
        if (Test-Path -LiteralPath $path -PathType Container) { $files += Get-ChildItem -LiteralPath $path -File -Recurse }
        elseif (Test-Path -LiteralPath $path -PathType Leaf) { $files += Get-Item -LiteralPath $path }
    }
    if (-not $files) { throw 'Arquivos-fonte Android não encontrados para comparação.' }
    $manifest = New-Object System.Text.StringBuilder
    foreach ($file in ($files | Sort-Object FullName -Unique)) {
        $relative = $file.FullName.Substring($androidRoot.Length).TrimStart('\','/').Replace('\','/')
        $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
        if ($relative -eq 'app/build.gradle') {
            $text = [System.Text.Encoding]::UTF8.GetString($bytes)
            $text = [regex]::Replace($text, "(?m)^\s*versionCode\s+\d+\s*$", 'versionCode <VERSION_CODE>')
            $text = [regex]::Replace($text, "(?m)^\s*versionName\s+'[^']*'\s*$", "versionName '<VERSION_NAME>'")
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
        }
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try { $fileHash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
        finally { $sha.Dispose() }
        [void]$manifest.Append($relative).Append("`n").Append($fileHash).Append("`n")
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($manifest.ToString())))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Get-GitPath {
    $cmd = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $paths = @((Join-Path $env:ProgramFiles 'Git\cmd\git.exe'),(Join-Path ${env:ProgramFiles(x86)} 'Git\cmd\git.exe'),(Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd\git.exe'),(Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'))
    foreach ($path in $paths) { if (Test-Path -LiteralPath $path) { return $path } }
    throw 'Git não foi encontrado no PATH nem nos caminhos locais conhecidos.'
}

function Get-Sha256([string] $Path) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
}

try {
    $metadataPath = Join-Path $ProjectRoot 'backend\static\app-updates\latest.json'
    $catalogPath = Join-Path $ProjectRoot 'backend\static\app-updates\catalog.json'
    $changelogPath = Join-Path $ProjectRoot 'backend\static\app-updates\CHANGELOG-APP.md'
    $metadata = Get-Content -LiteralPath $metadataPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($field in @('versionName','versionCode','packageName','sha256','sizeBytes','apkFile','apkUrl','sourceFingerprint')) {
        if ([string]$metadata.$field -ne [string]$catalog.$field) { throw "latest.json e catalog.json divergem em $field." }
    }
    if ($metadata.packageName -ne 'br.com.meninadosraios.vendas' -or $metadata.apkFile -ne 'Menina-dos-Raios-Vendas-OFICIAL.apk') { throw 'O catálogo não identifica o APK oficial direct.' }

    $fingerprint = Get-AndroidSourceFingerprint $ProjectRoot
    $git = Get-GitPath
    Push-Location -LiteralPath $ProjectRoot
    try {
        $branch = (& $git branch --show-current).Trim()
        if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'Atualizações e publicações do APK precisam estar em main.' }
        & $git fetch origin main
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível atualizar a referência origin/main.' }
        $head = (& $git rev-parse HEAD).Trim()
        $origin = (& $git rev-parse origin/main).Trim()
        if ($LASTEXITCODE -ne 0 -or $head -ne $origin) { throw 'main local precisa estar sincronizada com origin/main antes da publicação.' }

        if ($CheckOnly) {
            if (-not $metadata.sourceFingerprint) { Write-Host "APK_SOURCE_BASELINE_MISSING fingerprint=$fingerprint" -ForegroundColor Yellow }
            elseif ($metadata.sourceFingerprint -eq $fingerprint) { Write-Host "APK_ALREADY_CURRENT version=$($metadata.versionName) code=$($metadata.versionCode) fingerprint=$fingerprint" -ForegroundColor Green }
            else { Write-Host "APK_UPDATE_REQUIRED published=$($metadata.versionName) sourceFingerprint=$fingerprint" -ForegroundColor Yellow }
            return
        }

        $versionFile = Join-Path $ProjectRoot 'android\app\build.gradle'
        $versionSource = Get-Content -LiteralPath $versionFile -Raw
        $declaredNameBeforeBuild = [regex]::Match($versionSource,"(?m)^\s*versionName\s+'([^']+)'\s*$")
        $declaredCodeBeforeBuild = [regex]::Match($versionSource,'(?m)^\s*versionCode\s+(\d+)\s*$')
        $sourceVersionChanged = $declaredNameBeforeBuild.Success -and $declaredCodeBeforeBuild.Success -and ($declaredNameBeforeBuild.Groups[1].Value -ne [string]$metadata.versionName -or [int]$declaredCodeBeforeBuild.Groups[1].Value -ne [int]$metadata.versionCode)
        if ($metadata.sourceFingerprint -and ($metadata.sourceFingerprint -ne $fingerprint -or $sourceVersionChanged)) {
            Write-Host 'Alteração Android detectada: criando uma nova versão e compilando o APK direct assinado.' -ForegroundColor Cyan
            $parts = [regex]::Match([string]$metadata.versionName,'^(\d+)\.(\d+)\.(\d+)$')
            if (-not $parts.Success) { throw 'versionName precisa seguir o formato X.Y.Z para incremento automático.' }
            $newVersion = '{0}.{1}.{2}' -f $parts.Groups[1].Value,$parts.Groups[2].Value,([int]$parts.Groups[3].Value + 1)
            $newCode = [int]$metadata.versionCode + 1
            $gradleFile = Join-Path $ProjectRoot 'android\app\build.gradle'
            $gradleText = Get-Content -LiteralPath $gradleFile -Raw
            $declaredName = [regex]::Match($gradleText,"(?m)^\s*versionName\s+'([^']+)'\s*$")
            $declaredCode = [regex]::Match($gradleText,'(?m)^\s*versionCode\s+(\d+)\s*$')
            if ($declaredName.Success -and $declaredCode.Success -and [int]$declaredCode.Groups[1].Value -gt [int]$metadata.versionCode) {
                $newVersion = $declaredName.Groups[1].Value
                $newCode = [int]$declaredCode.Groups[1].Value
            }
            $gradleText = [regex]::Replace($gradleText,"(?m)^\s*versionCode\s+\d+\s*$", "        versionCode $newCode",1)
            $gradleText = [regex]::Replace($gradleText,"(?m)^\s*versionName\s+'[^']*'\s*$", "        versionName '$newVersion'",1)
            $utf8NoBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
            [System.IO.File]::WriteAllText($gradleFile,$gradleText,$utf8NoBom)
            $releaseNotes = 'Tela inicial com módulos complementares compactos; atualização mostra progresso do download e do envio ao instalador Android.'

            $sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
            $buildTools = Get-ChildItem -LiteralPath (Join-Path $sdk 'build-tools') -Directory | Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
            if (-not $buildTools) { throw 'Android SDK build-tools não encontrado.' }
            $javaHome = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr'
            if (Test-Path -LiteralPath (Join-Path $javaHome 'bin\java.exe')) { $env:JAVA_HOME=$javaHome; $env:PATH=(Join-Path $javaHome 'bin')+';'+$env:PATH }
            $initScript = Join-Path $env:TEMP 'menina-gradle-builddir.init.gradle'
            if (-not (Test-Path -LiteralPath $initScript)) { Set-Content -LiteralPath $initScript -Value "allprojects { p ->`n    p.buildDir = new File(System.getenv('TEMP'), 'menina-gradle-output/' + p.name)`n}`n" -Encoding ASCII }
            $gradle = Join-Path $ProjectRoot 'android\gradlew.bat'
            if (-not (Test-Path -LiteralPath $gradle)) { throw 'android\gradlew.bat não encontrado.' }
            Write-Host 'Compilando :app:assembleDirectRelease...' -ForegroundColor Cyan
            Push-Location -LiteralPath (Join-Path $ProjectRoot 'android')
            try { & $gradle '--no-daemon' '--init-script' $initScript ':app:assembleDirectRelease'; if ($LASTEXITCODE -ne 0) { throw "Gradle falhou (exit $LASTEXITCODE)." } }
            finally { Pop-Location }
            $builtApk = Join-Path $env:TEMP 'menina-gradle-output\app\outputs\apk\direct\release\app-direct-release.apk'
            if (-not (Test-Path -LiteralPath $builtApk)) { throw "APK directRelease não encontrado em $builtApk." }

            $fingerprint = Get-AndroidSourceFingerprint $ProjectRoot
            $apkHash = Get-Sha256 $builtApk
            $apkSize = (Get-Item -LiteralPath $builtApk).Length
            $releaseNotes = $releaseNotes.Trim()
            $publishedAt = (Get-Date).ToString("yyyy-MM-dd'T'HH:mm:sszzz")
            $release = [ordered]@{versionName=$newVersion;versionCode=$newCode;packageName='br.com.meninadosraios.vendas';sha256=$apkHash;releaseNotes=$releaseNotes;notes=$releaseNotes;apkFile='Menina-dos-Raios-Vendas-OFICIAL.apk';apkUrl='https://sistema.meninadosraios.com.br/app-updates/Menina-dos-Raios-Vendas-OFICIAL.apk';sizeBytes=$apkSize;publishedAt=$publishedAt;sourceFingerprint=$fingerprint}
            $json = $release | ConvertTo-Json -Depth 5
            $jsonEncoding = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
            [System.IO.File]::WriteAllText($metadataPath,$json,$jsonEncoding)
            [System.IO.File]::WriteAllText($catalogPath,$json,$jsonEncoding)
            $changelog = Get-Content -LiteralPath $changelogPath -Raw -Encoding UTF8
            $changelog = [regex]::Replace($changelog,'(?m)^Versao estavel atual: `[^`]+`\.',"Versao estavel atual: ``$newVersion``.",1)
            $entry = "## [$newVersion] - $((Get-Date).ToString('dd/MM/yyyy'))`r`n`r`n- $releaseNotes`r`n`r`n"
            $firstRelease = [regex]::Match($changelog,'(?m)^## \[')
            if (-not $firstRelease.Success) { throw 'Changelog sem cabeçalho de release; publicação interrompida.' }
            $changelog = $changelog.Insert($firstRelease.Index,$entry)
            $utf8NoBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
            [System.IO.File]::WriteAllText($changelogPath,$changelog,$utf8NoBom)
            $androidChangelog = Join-Path $ProjectRoot 'android\CHANGELOG-APP.md'
            if (Test-Path -LiteralPath $androidChangelog) { [System.IO.File]::WriteAllText($androidChangelog,$changelog,$utf8NoBom) }

            $releasePaths = @('android/app/build.gradle','backend/static/app-updates/latest.json','backend/static/app-updates/catalog.json','backend/static/app-updates/CHANGELOG-APP.md','android/CHANGELOG-APP.md')
            $dirty = @(& $git status --porcelain --untracked-files=all)
            foreach ($line in $dirty) {
                if ($line.Length -lt 4) { continue }
                $path = $line.Substring(3)
                if ($path -like 'android/app/src/main/*' -or $path -in @('android/build.gradle','android/settings.gradle','android/gradle.properties','android/gradle/libs.versions.toml')) { $releasePaths += $path }
                elseif ($line.Substring(0,2) -ne '??' -and $path -notin $releasePaths) { throw "Arquivo rastreado alterado fora do escopo do APK: $path. Mantido sem commit." }
            }
            $releasePaths = @($releasePaths | Sort-Object -Unique)
            foreach ($path in $releasePaths) { & $git add -- $path; if ($LASTEXITCODE -ne 0) { throw "git add falhou em $path." } }
            & $git commit --only -m "Android ${newVersion}: $releaseNotes" -- $releasePaths
            if ($LASTEXITCODE -ne 0) { throw 'Commit da versão Android falhou.' }
            $head = (& $git rev-parse HEAD).Trim()
            Write-Host "Enviando a versão $newVersion para origin/main (commit $head)." -ForegroundColor Cyan
            & $git push origin main
            if ($LASTEXITCODE -ne 0) { throw 'Commit criado, mas push para origin/main falhou; publicação interrompida antes do servidor.' }
            $metadata = Get-Content -LiteralPath $metadataPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $candidateDir = Join-Path $env:TEMP ('menina-apk-release-build-' + $newVersion)
            New-Item -ItemType Directory -Path $candidateDir -Force | Out-Null
            $freshApk = Join-Path $candidateDir $metadata.apkFile
            Copy-Item -LiteralPath $builtApk -Destination $freshApk -Force
        }
        elseif (-not $metadata.sourceFingerprint) {
            throw 'A versão publicada ainda não possui sourceFingerprint. Use a atualização de baseline documentada antes do próximo APK.'
        }
    }
    finally { Pop-Location }

    if (-not (Select-String -LiteralPath $changelogPath -Pattern ('Versao estavel atual: `' + [regex]::Escape($metadata.versionName) + '`\.') -Quiet)) { throw 'Versão do changelog diverge do catálogo.' }

    $sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
    $buildTools = Get-ChildItem -LiteralPath (Join-Path $sdk 'build-tools') -Directory | Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
    if (-not $buildTools) { throw 'Android SDK build-tools não encontrado.' }
    $aapt = Join-Path $buildTools.FullName 'aapt.exe'; $apksigner = Join-Path $buildTools.FullName 'apksigner.bat'
    $javaHome = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr'
    if (Test-Path -LiteralPath (Join-Path $javaHome 'bin\java.exe')) { $env:JAVA_HOME=$javaHome; $env:PATH=(Join-Path $javaHome 'bin')+';'+$env:PATH }
    $candidates = @()
    if ($freshApk -and (Test-Path -LiteralPath $freshApk)) { $candidates += Get-Item -LiteralPath $freshApk }
    $standard = Join-Path $ProjectRoot 'android\app\build\outputs\apk\direct\release\app-direct-release.apk'
    if (Test-Path -LiteralPath $standard) { $candidates += Get-Item -LiteralPath $standard }
    foreach ($root in (Get-ChildItem -LiteralPath $env:TEMP -Directory -Filter 'menina-apk-release-*' -ErrorAction SilentlyContinue)) { $path=Join-Path $root.FullName $metadata.apkFile; if (Test-Path -LiteralPath $path) { $candidates += Get-Item -LiteralPath $path } }
    $apk = $null
    foreach ($candidate in ($candidates | Sort-Object LastWriteTime -Descending)) { if ($candidate.Length -eq [long]$metadata.sizeBytes -and (Get-Sha256 $candidate.FullName) -eq [string]$metadata.sha256) { $apk=$candidate; break } }
    if (-not $apk) { throw 'Nenhum APK local corresponde ao hash e tamanho oficiais. APK antigo não será enviado.' }
    $badging = & $aapt dump badging $apk.FullName 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0 -or $badging -notmatch "package: name='br\.com\.meninadosraios\.vendas' versionCode='$([int]$metadata.versionCode)' versionName='$([regex]::Escape([string]$metadata.versionName))'") { throw 'Package/versão dentro do APK diverge do catálogo.' }
    $oldPreference=$ErrorActionPreference; $ErrorActionPreference='Continue'
    try { $signature = & $apksigner verify --print-certs $apk.FullName 2>&1 | Out-String; $sigExit=$LASTEXITCODE }
    finally { $ErrorActionPreference=$oldPreference }
    $cert=[regex]::Match($signature,'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]{64})')
    if ($sigExit -ne 0 -or -not $cert.Success -or $cert.Groups[1].Value.ToLowerInvariant() -ne 'd9e833244c3a3db92428e83b6badb63a88058064fc1a2ee3996c799e60a16d3f') { throw 'Assinatura/certificado oficial do APK não validado.' }
    Write-Host ("APK_VALIDATED version={0} code={1} size={2} sha256={3}" -f $metadata.versionName,$metadata.versionCode,$apk.Length,$metadata.sha256) -ForegroundColor Green
    if ($ValidateOnly) { return }

    $releaseId=(Get-Date -Format 'yyyyMMdd_HHmmss')+'_'+$metadata.versionName+'_'+([string]$metadata.sha256).Substring(0,8)
    $packageDir=Join-Path $env:TEMP ('menina-apk-release-'+$releaseId); New-Item -ItemType Directory -Path $packageDir | Out-Null
    Copy-Item -LiteralPath $apk.FullName -Destination (Join-Path $packageDir $metadata.apkFile)
    Copy-Item -LiteralPath $metadataPath -Destination (Join-Path $packageDir 'latest.json')
    Copy-Item -LiteralPath $catalogPath -Destination (Join-Path $packageDir 'catalog.json')
    Copy-Item -LiteralPath $changelogPath -Destination (Join-Path $packageDir 'CHANGELOG-APP.md')
    Set-Content -LiteralPath (Join-Path $packageDir 'SHA256SUMS') -Value ([string]$metadata.sha256+'  '+$metadata.apkFile) -Encoding ASCII
    $remoteRunner=Join-Path $env:TEMP ('menina-apk-publish-'+$releaseId+'.ps1')
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'scripts\publish_apk_remote.ps1') -Destination $remoteRunner
    $powershell=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $argumentLine="-NoProfile -ExecutionPolicy Bypass -NoExit -File `"$remoteRunner`" -PackageDir `"$packageDir`" -ReleaseId `"$releaseId`""
    Start-Process -FilePath $powershell -WindowStyle Normal -ArgumentList $argumentLine
    Write-Host 'Janela externa de publicação aberta. O backup, SCP, checksum e GET público são verificados em etapas separadas.' -ForegroundColor Green
}
catch { Write-Host "PREPARACAO_APK=FALHOU $($_.Exception.Message)" -ForegroundColor Red; throw }
finally { Write-Host "Log de preparação: $transcript"; Stop-Transcript | Out-Null }
