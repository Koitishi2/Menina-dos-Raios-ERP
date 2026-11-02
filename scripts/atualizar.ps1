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
        if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
            $gitCandidates = @(
                (Join-Path $env:ProgramFiles 'Git\cmd'),
                (Join-Path ${env:ProgramFiles(x86)} 'Git\cmd'),
                (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd')
            )
            $runtimeRoot = Join-Path $env:USERPROFILE '.cache\codex-runtimes'
            if (Test-Path -LiteralPath $runtimeRoot) {
                $gitCandidates += Get-ChildItem -LiteralPath $runtimeRoot -Directory -ErrorAction SilentlyContinue |
                    ForEach-Object { Join-Path $_.FullName 'dependencies\native\git\cmd' }
            }
            foreach ($candidate in $gitCandidates) {
                if ($candidate -and (Test-Path -LiteralPath (Join-Path $candidate 'git.exe'))) {
                    $env:PATH = $candidate + ';' + $env:PATH
                    break
                }
            }
        }
        if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
            throw 'Git não está no PATH e não foi encontrado nas instalações locais conhecidas.'
        }
        $branch = (& git branch --show-current).Trim()
        if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'O atualizador do servidor exige a branch main.' }
        & git fetch origin main
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível atualizar a referência origin/main.' }
        $commit = (& git rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível identificar o commit atual.' }
        $originMain = (& git rev-parse origin/main).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível identificar origin/main.' }

        $releasePaths = @(& git diff --name-only HEAD)
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível identificar os arquivos alterados.' }
        $newBackendPaths = @(& git ls-files --others --exclude-standard -- backend tests)
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível identificar novos arquivos de backend/testes.' }
        $releasePaths = @($releasePaths + $newBackendPaths | Where-Object { $_ } | Sort-Object -Unique)
        $allowedReleasePath = '^(backend/|tests/|scripts/atualizar\.ps1$|scripts/deploy_server\.py$|ATUALIZAR\.bat$|atualizar\.bat$|README\.md$|AGENTS\.md$)'
        $unsupportedPaths = @($releasePaths | Where-Object { $_ -notmatch $allowedReleasePath })
        if ($unsupportedPaths.Count -gt 0) {
            throw ('Há arquivos alterados fora do escopo do ERP. Eles foram preservados: ' + ($unsupportedPaths -join ', '))
        }

        if ($releasePaths.Count -gt 0) {
            if ($originMain -ne $commit) {
                throw 'O main local diverge de origin/main enquanto há alterações. Atualize o checkout antes de preparar o envio.'
            }
            Write-Host 'Arquivos ERP/testes que serão salvos no main:' -ForegroundColor Cyan
            $releasePaths | ForEach-Object { Write-Host ('  ' + $_) }
            $confirmCommit = Read-Host 'Confirma criar um commit com exatamente estes arquivos e publicar no main? (s/N)'
            if ($confirmCommit.Trim().ToLowerInvariant() -ne 's') { throw 'Commit cancelado; nenhum arquivo foi enviado.' }
            & git add -- $releasePaths
            if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar os arquivos ERP selecionados.' }
            $defaultMessage = 'ERP update ' + (Get-Date -Format 'yyyy-MM-dd HH:mm')
            $commitMessage = Read-Host "Mensagem do commit (Enter usa: $defaultMessage)"
            if ([string]::IsNullOrWhiteSpace($commitMessage)) { $commitMessage = $defaultMessage }
            & git commit -m $commitMessage
            if ($LASTEXITCODE -ne 0) { throw 'O commit falhou; revise a mensagem e os arquivos selecionados.' }
            $commit = (& git rev-parse HEAD).Trim()
            if ($LASTEXITCODE -ne 0) { throw 'Não foi possível identificar o commit criado.' }
            Write-Host "Publicando commit $commit no origin/main..." -ForegroundColor Cyan
            & git push origin main
            if ($LASTEXITCODE -ne 0) { throw 'O commit foi criado localmente, mas o push para origin/main falhou; o servidor não foi atualizado.' }
        }
        else {
            $worktreeChanges = & git status --porcelain --untracked-files=no
            if ($LASTEXITCODE -ne 0 -or $worktreeChanges) { throw 'Há mudanças rastreadas que não puderam ser selecionadas para o envio.' }
            if ($commit -ne $originMain) {
                & git merge-base --is-ancestor origin/main HEAD
                $isAhead = ($LASTEXITCODE -eq 0)
                if (-not $isAhead) {
                    & git merge-base --is-ancestor HEAD origin/main
                    if ($LASTEXITCODE -eq 0) {
                        & git merge --ff-only origin/main
                        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível atualizar main em fast-forward.' }
                        $commit = (& git rev-parse HEAD).Trim()
                    }
                    else { throw 'main local e origin/main divergem; resolva a divergência antes do envio.' }
                }
                if ($isAhead) {
                    Write-Host "Publicando os commits locais de main (HEAD $commit) em origin/main..." -ForegroundColor Cyan
                    & git push origin main
                    if ($LASTEXITCODE -ne 0) { throw 'O push para origin/main falhou; o servidor não foi atualizado.' }
                }
            }
        }
        $originMain = (& git rev-parse origin/main).Trim()
        if ($LASTEXITCODE -ne 0 -or $originMain -ne $commit) { throw 'O commit local não corresponde a origin/main; não é seguro atualizar o servidor.' }

        Write-Host 'Executando os testes focados do backend...' -ForegroundColor Cyan
        $testTargets = @()
        if ($releasePaths -match 'boletos|backend/app\.py|backend/static/index\.html') { $testTargets += 'tests/test_boletos.py' }
        if ($releasePaths -match 'whatsapp|new_tempo') { $testTargets += 'tests/test_new_tempo_collections.py' }
        if ($testTargets.Count -eq 0) { $testTargets = @('tests/test_new_tempo_collections.py') }
        $testTargets = @($testTargets | Sort-Object -Unique)
        python -m pytest @testTargets -q
        if ($LASTEXITCODE -ne 0) { throw "Testes focados falharam (exit $LASTEXITCODE); o commit está no GitHub, mas o deploy foi interrompido." }
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
