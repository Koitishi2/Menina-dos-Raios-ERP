# Deployment Workflow

Follow this workflow whenever publishing this project to the server or publishing the Android APK.

## General

- Never open a visible Command Prompt or run a user-facing deployment through CMD inside Codex. Use an external, visible Windows PowerShell window so the user can enter SSH passwords there.
- Preserve the user's unrelated working-tree changes. Package, commit, and deploy only files needed for the requested release.
- Treat the backend and APK as separate deployment targets. Do not report either as published until its own remote validation succeeds.
- Keep the external PowerShell window open through completion and report the actual result and log path.
- Do not put credentials, private keys, or passwords in scripts, logs, or chat.

## Backend

- Use `scripts/deploy_server.py` from a clean worktree at the exact commit being deployed. The tool requires the commit to be pushed to `origin` first and the local ignored `atualizarrefatorado.local.bat` config to be present in that worktree.
- Run the project's focused tests and `python scripts/deploy_server.py --check` before connecting.
- Publish with `python scripts/deploy_server.py --apply` from external Windows PowerShell. Let its backup, checksum, preflight, promotion, and healthcheck complete; verify `RESULT=APPLY_OK` in the log. Do not rerun a backend deployment already confirmed successful.

## Android APK

- Select the official signed `direct` release APK and verify its package name, version name/code, signature certificate, size, and SHA-256 against both `latest.json` and `catalog.json` before upload.
- Windows PowerShell 5.1 on this machine does not provide `Get-FileHash` and does not support `SHA256.HashData`. Compute hashes with `[System.Security.Cryptography.SHA256]::Create().ComputeHash(...)`; dispose the hash object and file stream.
- Use the proven three-stage publication sequence in external PowerShell: (1) back up the current APK/catalog/changelog remotely, (2) SCP the official APK, `latest.json`, `catalog.json`, `CHANGELOG-APP.md`, and a SHA256SUMS file to a unique remote staging directory, (3) run `sha256sum -c` remotely before promoting the staged files to `/opt/menina/backend/static/app-updates`.
- Preserve a timestamped backup under `/root/menina_apk_backup_<release-id>`. Keep the SCP and final SSH checksum/promotion as distinct stages, and require explicit success markers such as `APK_PUBLISH_OK` and `PUBLICACAO_REMOTA=OK`.
- Update the changelog's current version and release entry to match catalog metadata before upload. After promotion, confirm the public `latest.json` version and SHA-256 match the APK; the remote checksum verification is authoritative if HTTP HEAD is unsupported.
- Use `C:\Users\bobif\AppData\Local\Temp\menina-apk-publish-2029-status.txt` as the reference record for the successful 2.0.29 flow and `menina-apk-publish-2030-status.txt` for the successful 2.0.30 flow. Both follow backup, SCP-to-staging, checksum validation, promotion.
