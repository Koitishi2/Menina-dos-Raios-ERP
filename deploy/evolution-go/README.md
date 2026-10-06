# Evolution Go bootstrap

This stack is isolated from the business backend and the existing Baileys service.
It pins Evolution Go `0.7.2`, keeps PostgreSQL private on its compose network, and
publishes the Manager/API only on `127.0.0.1:8766`. WhatsApp auto-connect is off.

Install from the repository root in PowerShell:

```powershell
& .\scripts\install_evolution_go.ps1
```

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
