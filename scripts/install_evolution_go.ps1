$ErrorActionPreference = 'Stop'

$server = 'root@2.24.124.76'
$port = 22
$root = Split-Path -Parent $PSScriptRoot
$bootstrap = Join-Path $env:TEMP ('menina-evolution-go-' + [guid]::NewGuid().ToString('N'))
$archive = Join-Path $env:TEMP ('menina-evolution-go-' + [guid]::NewGuid().ToString('N') + '.tar')
$remoteDir = '/tmp/menina-evolution-go-bootstrap'

foreach ($tool in 'ssh.exe', 'scp.exe', 'tar.exe') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "$tool não encontrado no PATH. Instale/ative OpenSSH Client e tar do Windows."
    }
}

$sourceDir = Join-Path $root 'deploy\evolution-go'
if (-not (Test-Path (Join-Path $sourceDir 'compose.yaml'))) {
    throw "Arquivos de instalação ausentes: $sourceDir"
}

New-Item -ItemType Directory -Path $bootstrap | Out-Null
try {
    New-Item -ItemType Directory -Path (Join-Path $bootstrap 'deploy\evolution-go') -Force | Out-Null
    Copy-Item (Join-Path $sourceDir 'compose.yaml') (Join-Path $bootstrap 'deploy\evolution-go\compose.yaml')
    Copy-Item (Join-Path $sourceDir 'init-users-db.sql') (Join-Path $bootstrap 'deploy\evolution-go\init-users-db.sql')
    Copy-Item (Join-Path $sourceDir 'resolv.conf') (Join-Path $bootstrap 'deploy\evolution-go\resolv.conf')
    Copy-Item (Join-Path $sourceDir 'install.sh') (Join-Path $bootstrap 'deploy\evolution-go\install.sh')
    Copy-Item (Join-Path $sourceDir 'manager-login-license-gate.patch') (Join-Path $bootstrap 'deploy\evolution-go\manager-login-license-gate.patch')

    & tar.exe -cf $archive -C $bootstrap deploy
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao empacotar arquivos da instalação.' }

    & ssh.exe -tt -p $port $server "install -d -m 700 $remoteDir"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar a pasta temporária remota.' }

    & scp.exe -P $port $archive "${server}:${remoteDir}/bootstrap.tar"
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao enviar o pacote de configuração.' }

    $remoteScript = "$remoteDir/deploy/evolution-go/install.sh"
    $remoteCommand = "set -e; tar -xf $remoteDir/bootstrap.tar -C $remoteDir; bash -n $remoteScript; bash $remoteScript"
    & ssh.exe -tt -p $port $server $remoteCommand
    if ($LASTEXITCODE -ne 0) { throw 'Instalação remota não concluiu. A configuração temporária foi preservada para diagnóstico.' }
}
finally {
    Remove-Item -LiteralPath $bootstrap -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
}
