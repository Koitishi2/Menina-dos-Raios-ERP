# Evolution Go bootstrap

This stack is isolated from the business backend and the existing Baileys service.
It builds upstream Evolution Go `0.7.2` at pinned commit
`9337afc47e10b86cc896a6f432240e40fee95dd1` with a minimal Manager-login fix,
keeps PostgreSQL private on its compose network, and publishes the Manager/API
only on `127.0.0.1:8766`. The existing Podman network is treated as external to
avoid Compose attempting to recreate it. WhatsApp auto-connect is off.

The upstream `0.7.2` Manager login preflights credentials with `GET /instance/all`,
but its global license gate returned `503` before the route's admin-key middleware
could validate the key. The patch lets only that preflight reach the existing
`AuthAdmin` check; all other unlicensed business routes remain gated.

The Evolution Go container mounts a dedicated `/etc/resolv.conf` with the tested
resolvers `1.1.1.1` and `8.8.8.8`. This bypasses the Podman network's non-responsive
DNS proxy for external lookups. PostgreSQL uses a fixed private IP, so the service
does not depend on container-name DNS. The installer verifies licensing-domain
resolution inside the container before reporting success.

Install from the repository root in PowerShell:

```powershell
& .\scripts\install_evolution_go.ps1
```

For routine access, double-click `scripts/ABRIR_EVOLUTION_GO.bat`. It creates a
local run log under `logs_evolution_go`, starts the SSH connection through the
`EVOLUTION_GO_CONEXAO.bat` helper (or `EVOLUTION_GO_MONITOR.bat` if the tunnel
already exists), waits up to 90 seconds for the health endpoint, and then opens
the Manager. The SSH window streams the Evolution Go container logs without
filtering so connection, container, and HTTP errors remain visible. The stream is appended to
`/root/evolution-go-manager.log` with root-only permissions. API keys and request
headers are not logged by this script. Keep the SSH window open while testing;
use `Ctrl+C` there to stop the stream after the login attempt.

The script uploads only these bootstrap files and runs the idempotent installer as
root over SSH. It creates `/opt/menina/evolution-go/.env` with mode `0600`; secrets
are generated on the server and are never stored in Git. The operator email is
intentionally left empty so booting the unlicensed service does not attempt
automatic license activation.

When ready for the first manual registration, open a second PowerShell and run:

```powershell
ssh.exe -L 8766:127.0.0.1:8766 -p 22 root@2.24.124.76
```

Keep that SSH session open, then browse to `http://localhost:8766/manager/login`.
Complete the licensing flow there. The first registration requires browser-based
identity verification (Magic Link or OAuth). Only after that registration should
`EVOLUTION_OPERATOR_EMAIL` be set in the private server `.env` for optional
idempotent activation on future deployments.

That automatic endpoint treats the registered email as its proof of identity and
does not require a second factor. Keep the email unset until the first manual
registration is complete and do not expose the private `.env` or API key.

Evolution Go remains unselected in the ERP until separately integrated and tested.
The existing Baileys service and its QR/session data are not changed by this
bootstrap. The Evolution Go usage notice must be visible to administrators and
available in system documentation/settings before integrating it into the ERP.
Do not delete the named volumes `menina_evolution_go_*` during rollback.
