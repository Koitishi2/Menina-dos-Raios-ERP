param([Parameter(Mandatory = $true)] [string] $ProjectRoot)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$transcript = Join-Path $env:TEMP ('menina-atualizar-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '-status.txt')
Start-Transcript -Path $transcript -Force | Out-Null

try {
    Write-Host 'ATUALIZADOR MENINA DOS RAIOS' -ForegroundColor Green
    Write-Host '1. Publicar APK oficial'
    Write-Host '2. Atualizar servidor ERP'
    Write-Host '0. Sair'
    $choice = Read-Host 'Escolha o destino'

    if ($choice -eq '1') {
        & (Join-Path $ProjectRoot 'scripts\prepare_apk_publish.ps1') -ProjectRoot $ProjectRoot
    }
    elseif ($choice -eq '2') {
        Set-Location -LiteralPath $ProjectRoot
        $branch = (& git branch --show-current).Trim()
        if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'O atualizador do servidor exige a branch main.' }
        $commit = (& git rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível identificar o commit atual.' }
        $dirty = & git status --porcelain --untracked-files=no
        if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Existem alterações rastreadas sem commit; o servidor não foi atualizado.' }
        & git fetch origin main
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível atualizar a referência origin/main.' }
        $originMain = (& git rev-parse origin/main).Trim()
        if ($originMain -ne $commit) { throw 'O commit local não corresponde a origin/main; publique o main antes do envio.' }
        Write-Host 'Executando os testes focados do backend...' -ForegroundColor Cyan
        python -m pytest tests/test_new_tempo_collections.py -q
        if ($LASTEXITCODE -ne 0) { throw "Testes focados falharam (exit $LASTEXITCODE)." }
        Write-Host 'Validando o pacote do servidor antes da conexão...' -ForegroundColor Cyan
        python scripts/deploy_server.py --check
        if ($LASTEXITCODE -ne 0) { throw "Preflight do servidor falhou (exit $LASTEXITCODE)." }
        Write-Host 'Iniciando a atualização do servidor. Confirme com s quando solicitado e digite as senhas SSH nesta janela.' -ForegroundColor Yellow
        python scripts/deploy_server.py --apply
        if ($LASTEXITCODE -ne 0) { throw "Atualização do servidor falhou (exit $LASTEXITCODE)." }
        $deployLog = Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'logs_deploy') -Filter ('deploy_*_' + $commit.Substring(0, 12) + '.log') -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $deployLog -or (Get-Content -LiteralPath $deployLog.FullName -Raw) -notmatch ('RESULT=APPLY_OK COMMIT=' + [regex]::Escape($commit))) {
            throw 'O processo terminou sem RESULT=APPLY_OK para o commit enviado.'
        }
        Write-Host "RESULT=APPLY_OK COMMIT=$commit" -ForegroundColor Green
        Write-Host 'PUBLICACAO_SERVIDOR=OK' -ForegroundColor Green
    }
    elseif ($choice -ne '0') { throw 'Opção inválida.' }
    if ($choice -eq '1' -or $choice -eq '0') { exit 0 }
}
catch {
    Write-Host "ATUALIZACAO=FALHOU $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Write-Host "Log: $transcript"
    Stop-Transcript | Out-Null
}
