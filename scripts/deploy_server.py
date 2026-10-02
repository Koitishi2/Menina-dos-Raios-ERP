import argparse
import datetime as dt
import hashlib
import os
import re
import shlex
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_deploy_package.py"
REMOTE_SCRIPT = ROOT / "atualizar_backend_seguro.sh"
CONFIG_FILE = ROOT / "atualizarrefatorado.local.bat"
SAFE_VALUE = re.compile(r"^[A-Za-z0-9_./:@+-]+$")


class DeployError(RuntimeError):
    def __init__(self, stage, message):
        super().__init__(message)
        self.stage = stage


class RunLog:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = path.open("w", encoding="utf-8", newline="\n")

    def write(self, message):
        stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        line = f"{stamp} {message}"
        print(line, flush=True)
        self.file.write(line + "\n")
        self.file.flush()

    def close(self):
        self.file.close()


def run_command(command, log, stage, cwd=ROOT, env=None, check=True):
    log.write(f"[{stage}] $ {' '.join(shlex.quote(str(part)) for part in command)}")
    process = subprocess.Popen(
        [str(part) for part in command], cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace", bufsize=1,
    )
    for line in process.stdout:
        log.write(line.rstrip("\r\n"))
    code = process.wait()
    if check and code:
        raise DeployError(stage, f"comando terminou com codigo {code}")
    return code


def read_local_config():
    values = {}
    if not CONFIG_FILE.is_file():
        raise DeployError("CONFIG", "arquivo atualizarrefatorado.local.bat ausente")
    for line in CONFIG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r'^\s*set\s+"([A-Za-z0-9_]+)=(.*)"\s*$', line, re.I)
        if match:
            values[match.group(1).upper()] = match.group(2).strip()
    return values


def validate_config(values):
    required = (
        "HOST", "PORT", "USER", "REMOTE_BACKEND_DIR",
        "REMOTE_STAGING_DIR", "REMOTE_BACKUP_DIR",
    )
    missing = [key for key in required if not values.get(key) or "CONFIGURAR" in values[key].upper()]
    if missing:
        raise DeployError("CONFIG", "preencha no arquivo local: " + ", ".join(missing))
    for key in required:
        if not SAFE_VALUE.fullmatch(values[key]):
            raise DeployError("CONFIG", f"valor invalido para {key}")
    if not values["PORT"].isdigit():
        raise DeployError("CONFIG", "PORT precisa ser numerica")
    expected = {
        "REMOTE_BACKEND_DIR": "/opt/menina/backend",
        "REMOTE_STAGING_DIR": "/root/menina_refatoracao_staging",
        "REMOTE_BACKUP_DIR": "/root/menina_refatoracao_backups",
    }
    for key, value in expected.items():
        if values[key] != value:
            raise DeployError("CONFIG", f"{key} nao corresponde ao caminho permitido pelo atualizador")
    health_url = values.get("HEALTHCHECK_URL", "")
    if health_url:
        parsed = urlparse(health_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise DeployError("CONFIG", "HEALTHCHECK_URL precisa ser uma URL HTTPS sem credenciais")


def parse_builder_output(text):
    result = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    for key in ("PACKAGE", "PACKAGE_SHA256", "MANIFEST", "CHECKSUMS", "FILE_COUNT"):
        if not result.get(key):
            raise DeployError("PACKAGE", f"empacotador nao retornou {key}")
    return result


def package_python_count(package_path):
    with zipfile.ZipFile(package_path) as archive:
        return sum(
            1 for name in archive.namelist()
            if name.startswith("backend/") and name.count("/") == 1 and name.endswith(".py")
        )


def safe_remote(value):
    if not SAFE_VALUE.fullmatch(value):
        raise DeployError("CONFIG", "valor remoto contem caracteres nao permitidos")
    return shlex.quote(value)


def remote_call(config, command, log, stage, check=True):
    return run_command(
        ["ssh", "-o", "ConnectTimeout=15", "-p", config["PORT"],
         f"{config['USER']}@{config['HOST']}", command],
        log, stage, check=check,
    )


def fetch_remote_diagnostics(config, run_dir, log):
    stage_dir = safe_remote(run_dir)
    command = (
        f"for f in {stage_dir}/deploy.log {stage_dir}/deploy_status.log; do "
        "if test -f \"$f\"; then echo ====\ \"$f\"; tail -n 160 \"$f\"; fi; done"
    )
    remote_call(config, command, log, "REMOTE-DIAGNOSTICS", check=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Publica no servidor um commit ja enviado ao GitHub.")
    parser.add_argument("--check", action="store_true", help="monta e valida o pacote local; nao conecta ao servidor")
    parser.add_argument("--remote-dry-run", action="store_true", help="valida no staging remoto sem aplicar")
    parser.add_argument("--apply", action="store_true", help="aplica no servidor e exige confirmacao")
    args = parser.parse_args(argv)
    if sum((args.check, args.remote_dry_run, args.apply)) > 1:
        parser.error("use somente um modo por execucao")
    mode = "apply" if args.apply else "remote-dry-run" if args.remote_dry_run else "check"
    run_id = dt.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    commit = "unknown"
    log = None
    stage = "GIT"
    run_dir = None
    config = None
    remote_stage_created = False

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        log_path = ROOT / "logs_deploy" / f"deploy_{run_id}_{commit[:12]}.log"
        log = RunLog(log_path)
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        log.write(f"RUN_ID={run_id} MODE={mode} BRANCH={branch} COMMIT={commit}")
        if dirty:
            raise DeployError("GIT", "ha alteracoes rastreadas sem commit; publique e commit antes do deploy")

        release_dir = ROOT / "backups" / "deploy_runs" / run_id
        package_dir = release_dir / "package"
        package_dir.mkdir(parents=True, exist_ok=True)
        stage = "PACKAGE"
        build = subprocess.run(
            [sys.executable, str(BUILDER), "--commit", commit,
             "--output-dir", str(package_dir)], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        for line in (build.stdout + build.stderr).splitlines():
            log.write(f"[PACKAGE] {line}")
        if build.returncode:
            raise DeployError("PACKAGE", f"geracao do pacote falhou (codigo {build.returncode})")
        package = parse_builder_output(build.stdout)
        package_path = Path(package["PACKAGE"])
        package_hash = hashlib.sha256(package_path.read_bytes()).hexdigest().upper()
        if package_hash != package["PACKAGE_SHA256"].upper():
            raise DeployError("PACKAGE", "hash calculado diverge do empacotador")
        package_name = package_path.name
        script_hash = hashlib.sha256(REMOTE_SCRIPT.read_bytes()).hexdigest().upper()
        py_count = package_python_count(package_path)
        log.write(
            f"PACKAGE={package_name} SHA256={package_hash} FILES={package['FILE_COUNT']} "
            f"BACKEND_ROOT_PY={py_count} MANIFEST={package['MANIFEST']} CHECKSUMS={package['CHECKSUMS']}"
        )

        if mode == "check":
            log.write("NEXT=ATUALIZAR.bat --remote-dry-run; depois ATUALIZAR.bat --apply")
            log.write("RESULT=LOCAL_CHECK_OK SSH=NOT_RUN")
            print("Nenhuma conexao foi feita. Proximos passos: --remote-dry-run e depois --apply.")
            print(f"Log local: {log_path}")
            return 0

        stage = "CONFIG"
        config = read_local_config()
        validate_config(config)
        if not py_count:
            raise DeployError("PACKAGE", "pacote nao contem Python do backend na raiz")
        update_key = f"{run_id}_{commit[:12]}"
        run_dir = f"{config['REMOTE_STAGING_DIR']}/quick_{update_key}"
        backup_dir = f"{config['REMOTE_BACKUP_DIR']}/quick_{update_key}"
        remote_pkg = f"{run_dir}/{package_name}"
        remote_script = f"{run_dir}/{REMOTE_SCRIPT.name}"
        remote_checksums = f"{run_dir}/{Path(package['CHECKSUMS']).name}"
        log.write(f"REMOTE={config['USER']}@{config['HOST']}:{config['REMOTE_BACKEND_DIR']}")
        log.write(f"REMOTE_STAGE={run_dir} BACKUP={backup_dir}")

        if mode == "apply":
            print("\nO pacote acima sera aplicado no servidor. Os dados persistentes serao preservados.")
            if input("Confirma a publicacao? [s/N] ").strip().lower() not in {"s", "sim"}:
                raise DeployError("CONFIRM", "publicacao cancelada")

        stage = "REMOTE-STAGING"
        remote_directories = safe_remote(run_dir)
        if mode == "apply":
            remote_directories += " " + safe_remote(backup_dir)
        remote_call(
            config,
            f"set -e; test {safe_remote(config['REMOTE_BACKEND_DIR'])} != /; "
            f"mkdir -p {remote_directories}",
            log, stage,
        )
        remote_stage_created = True
        for local_path, target in (
            (package_path, remote_pkg),
            (Path(package["CHECKSUMS"]), remote_checksums),
            (REMOTE_SCRIPT, remote_script),
        ):
            run_command(
                ["scp", "-o", "ConnectTimeout=15", "-P", config["PORT"],
                 str(local_path), f"{config['USER']}@{config['HOST']}:{target}"],
                log, "SCP",
            )

        stage = "REMOTE-CHECKSUM"
        verify_dir = f"{run_dir}/package_verify"
        remote_call(
            config,
            f"set -e; cd {safe_remote(run_dir)}; "
            f"test \"$(sha256sum {safe_remote(package_name)} | awk '{{print toupper($1)}}')\" = {safe_remote(package_hash)}; "
            f"test \"$(sha256sum {safe_remote(REMOTE_SCRIPT.name)} | awk '{{print toupper($1)}}')\" = {safe_remote(script_hash)}; "
            f"test \"$(sha256sum {safe_remote(Path(package['CHECKSUMS']).name)} | awk '{{print toupper($1)}}')\" = "
            f"{safe_remote(hashlib.sha256(Path(package['CHECKSUMS']).read_bytes()).hexdigest().upper())}; "
            f"mkdir {safe_remote(verify_dir)}; "
            f"python3 -m zipfile -e {safe_remote(package_name)} {safe_remote(verify_dir)}; "
            f"cd {safe_remote(verify_dir)}; "
            f"tail -n +2 {safe_remote('../' + Path(package['CHECKSUMS']).name)} | sha256sum -c -",
            log, stage,
        )

        stage = "REMOTE-APPLY" if mode == "apply" else "REMOTE-DRY-RUN"
        apply_env = {
            "RUN_DIR": run_dir,
            "APP_DIR": config["REMOTE_BACKEND_DIR"],
            "BACKUP_DIR": backup_dir,
            "SERVICE": "menina",
            "EXPECTED_PY_COUNT": str(py_count),
            "PACKAGE_NAME": package_name,
            "EXPECTED_PACKAGE_SHA256": package_hash,
            "EXPECTED_SCRIPT_SHA256": script_hash,
            "DEPLOY_RUN_ID": run_id,
            "DEPLOY_COMMIT": commit,
            "DRY_RUN": "0" if mode == "apply" else "1",
        }
        if mode == "apply":
            if not config.get("HEALTHCHECK_URL"):
                raise DeployError("CONFIG", "HEALTHCHECK_URL nao configurado no arquivo local")
            apply_env["HEALTHCHECK_URL"] = config["HEALTHCHECK_URL"]
        assignments = " ".join(f"{key}={safe_remote(value)}" for key, value in apply_env.items())
        remote_call(config, f"{assignments} bash {safe_remote(remote_script)}", log, stage)
        fetch_remote_diagnostics(config, run_dir, log)

        stage = "REMOTE-CLEANUP"
        remote_call(
            config,
            f"set -e; case {safe_remote(run_dir)} in {safe_remote(config['REMOTE_STAGING_DIR'])}/quick_*) "
            f"rm -rf -- {safe_remote(run_dir)} ;; *) echo INVALID_STAGING_PATH >&2; exit 90 ;; esac",
            log, stage,
        )
        result_line = f"RESULT={mode.upper().replace('-', '_')}_OK COMMIT={commit}"
        if mode == "apply":
            result_line += f" BACKUP={backup_dir}"
        log.write(result_line)
        print(f"\nConcluido. Log local: {log_path}")
        if mode == "apply":
            print(f"Backup remoto de codigo: {backup_dir}")
        return 0
    except DeployError as exc:
        if log:
            log.write(f"RESULT=FAILED STAGE={exc.stage} ERROR={exc}")
            if config and run_dir and remote_stage_created:
                fetch_remote_diagnostics(config, run_dir, log)
                log.write(f"REMOTE_STAGE_PRESERVED={run_dir}")
            print(f"\nFalha na etapa {exc.stage}: {exc}")
            print(f"Consulte o log: {log.path}")
            if config and run_dir and remote_stage_created:
                print(f"Staging remoto preservado: {run_dir}")
        else:
            print(f"Falha na etapa {exc.stage}: {exc}", file=sys.stderr)
        return 1
    except (OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        if log:
            log.write(f"RESULT=FAILED STAGE={stage} ERROR={type(exc).__name__}: {exc}")
            if config and run_dir and remote_stage_created:
                fetch_remote_diagnostics(config, run_dir, log)
                log.write(f"REMOTE_STAGE_PRESERVED={run_dir}")
            print(f"\nFalha na etapa {stage}: {exc}")
            print(f"Consulte o log: {log.path}")
            if config and run_dir and remote_stage_created:
                print(f"Staging remoto preservado: {run_dir}")
        else:
            print(f"Falha na etapa {stage}: {exc}", file=sys.stderr)
        return 1
    finally:
        if log:
            log.close()


if __name__ == "__main__":
    raise SystemExit(main())
