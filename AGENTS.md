# Deployment Workflow

Follow this workflow whenever publishing this project to the server or publishing the Android APK.

## General

- All new commits and publications must use `main`. Do not create branches or additional worktrees unless the user explicitly requests them. Keep `origin/main` current with the approved ERP and Android updates.
- The Android source is maintained in `android/` in this repository. Keep signing keys, credentials, local configuration, and generated APKs outside Git.
- Never open a visible Command Prompt or run a user-facing deployment through CMD inside Codex. Use an external, visible Windows PowerShell window so the user can enter SSH passwords there.
- Preserve the user's unrelated working-tree changes. Package, commit, and deploy only files needed for the requested release.
- Treat the backend and APK as separate deployment targets. Do not report either as published until its own remote validation succeeds.
- Keep the external PowerShell window open through completion and report the actual result and log path.
- Do not put credentials, private keys, or passwords in scripts, logs, or chat.

## Backend

- Use `scripts/deploy_server.py` from the clean existing `main` checkout at the exact commit being deployed. Push that commit to `origin/main` first and retain the ignored `atualizarrefatorado.local.bat` locally. Do not create a release branch or another worktree.
- Run the project's focused tests and `python scripts/deploy_server.py --check` before connecting.
- Publish with `python scripts/deploy_server.py --apply` from external Windows PowerShell. Let its backup, checksum, preflight, promotion, and healthcheck complete; verify `RESULT=APPLY_OK` in the log. Do not rerun a backend deployment already confirmed successful.

## Android APK

- Select the official signed `direct` release APK and verify its package name, version name/code, signature certificate, size, and SHA-256 against both `latest.json` and `catalog.json` before upload.
- Windows PowerShell 5.1 on this machine does not provide `Get-FileHash` and does not support `SHA256.HashData`. Compute hashes with `[System.Security.Cryptography.SHA256]::Create().ComputeHash(...)`; dispose the hash object and file stream.
- Use the proven three-stage publication sequence in external PowerShell: (1) back up the current APK/catalog/changelog remotely, (2) SCP the official APK, `latest.json`, `catalog.json`, `CHANGELOG-APP.md`, and a SHA256SUMS file to a unique remote staging directory, (3) run `sha256sum -c` remotely before promoting the staged files to `/opt/menina/backend/static/app-updates`.
- Preserve a timestamped backup under `/root/menina_apk_backup_<release-id>`. Keep the SCP and final SSH checksum/promotion as distinct stages, and require explicit success markers such as `APK_PUBLISH_OK` and `PUBLICACAO_REMOTA=OK`.
- Update the changelog's current version and release entry to match catalog metadata before upload. After promotion, confirm the public `latest.json` version and SHA-256 match the APK; the remote checksum verification is authoritative if HTTP HEAD is unsupported.
- Use `C:\Users\bobif\AppData\Local\Temp\menina-apk-publish-2029-status.txt` as the reference record for the successful 2.0.29 flow and `menina-apk-publish-2030-status.txt` for the successful 2.0.30 flow. Both follow backup, SCP-to-staging, checksum validation, promotion.

## External PowerShell Pattern

- Save each release runner as a `.ps1` file in `%TEMP%`; do not build a long SSH command inline. Open it in a visible, interactive PowerShell 5.1 window with:

  ```powershell
  Start-Process -FilePath "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-File', "$env:TEMP\<release-script>.ps1")
  ```

- The release runner must print which phase is starting before invoking SSH/SCP. Let SSH/SCP request passwords interactively in that window; never pass a password as an argument or store it in the script/transcript.
- Start a transcript at the beginning, keep the window open after completion, and print the log path plus separate backend/APK results. Catch failures without converting them into success.
- Backend sequence: run `python scripts/deploy_server.py --apply`, answer its explicit confirmation with `s`, enter SSH passwords in the visible window, then require the log marker `RESULT=APPLY_OK` for the exact deployed commit. Do not repeat a backend run after this marker and its healthcheck are confirmed.
- APK sequence: prevalidate the official signed APK and matching metadata before opening the release window; create a timestamped remote backup; SCP APK, catalogs, changelog, and SHA256SUMS to a unique staging path; remotely run `sha256sum -c` before atomic promotion; require remote checksum success and `APK_PUBLISH_OK`.
- After promotion, verify the public `latest.json` and `catalog.json` version/code/hash/size, then GET the APK and hash the downloaded bytes. HTTP HEAD may return 405 and is not a publication failure when GET plus checksum succeeds.
- Keep nested shell quoting out of the final remote success test. Print `cat latest.json` after remote checksums and compare its parsed fields locally with `Invoke-RestMethod`; nested PowerShell/SSH/grep quotes caused a false failure after the 2.0.33 files had already been promoted.
- In Windows PowerShell 5.1, `apksigner.bat` can emit Java restricted-method warnings that interact badly with `$ErrorActionPreference = 'Stop'`. Verify APK signature before the publication runner; do not rerun `apksigner` inside the SSH/SCP publication script. Treat native command exit codes (`$LASTEXITCODE`) as authoritative.
- Compute SHA-256 with `[System.Security.Cryptography.SHA256]::Create()` and dispose the object (and any file stream); do not use `Get-FileHash` or `SHA256.HashData` on this machine.
- Successful reference run on 2026-10-20: backend commit `7d9d0c3c2987cb36977f612ef36c1045ac281af1`, `RESULT=APPLY_OK`; APK `2.0.33`/61, SHA-256 `8adde04dbd32c5bc4a1a688cb4f1c101ba342da9368f73856976ed38cc7dbf13`, remote backup `/root/menina_apk_backup_20261020_2.0.33_8adde04d`. APK public GET and metadata/hash/size matched. The runner's nested-quote final grep failed after remote checksums and promotion; use public GET validation as described above and do not copy that grep implementation.

## Local update launchers

- `atualizar_apk.bat` is the canonical launcher for every Android APK publication. It validates and publishes only the official APK through an external Windows PowerShell 5.1 window; use it for future APK sends.
- `atualizar apk.bat` remains a compatibility alias to `atualizar_apk.bat`.
- `ATUALIZAR.bat` (the same filename as `atualizar.bat` on Windows) opens a menu for the APK or ERP server workflow.
- `PUBLICAR_APK.bat` remains a compatibility shortcut to `atualizar apk.bat`.
- The launchers copy their PowerShell runner to `%TEMP%`; enter SSH passwords only in the visible PowerShell window and confirm the matching remote success marker before reporting completion.
- Public APK validation must tolerate transiently truncated GET responses: use `curl.exe` with bounded retries and a cache-busting query on each attempt; only accept HTTP 200 when both expected file size and SHA-256 match. A failed first GET is not publication failure if a later retry verifies; report failure if all retries fail.
- Successful canonical launcher reference, 2026-10-29: `atualizar_apk.bat` published APK `2.0.45`/73. Backup `/root/menina_apk_backup_20261029_175348_2.0.45_808b5a6c`; remote staging checksum passed; public GET attempt 1/4 verified size `2759094` and SHA-256 `808b5a6c26fe6095e013616ec08d8cf5aa0590486922e1994e6310541fe77504`, ending with `APK_PUBLISH_OK ... PUBLIC_GET=OK` and `PUBLICACAO_REMOTA=OK`. Keep this launcher and retry policy as the standard for future APK sends.
