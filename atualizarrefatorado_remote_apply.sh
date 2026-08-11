set -eu

cd "$REMOTE_RUN_DIR"
printf '%s  %s\n' "$EXPECTED_SHA" "$ZIP_NAME" > SHA256SUMS
$REMOTE_HASH_TOOL -c SHA256SUMS

mkdir pkg
$REMOTE_UNZIP_TOOL "$ZIP_NAME" pkg

python3 <<'PY'
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import urllib.request

run_dir = pathlib.Path(os.environ["REMOTE_RUN_DIR"]).resolve()
pkg_dir = run_dir / "pkg"
app_dir = pathlib.Path(os.environ["REMOTE_APP_DIR"]).resolve()
backup_file = pathlib.Path(os.environ["REMOTE_BACKUP_FILE"]).resolve()
app_files = [item for item in os.environ["APP_FILES"].split() if item]
restart_cmd = os.environ["REMOTE_SERVICE_RESTART"].split()
healthcheck_url = os.environ.get("HEALTHCHECK_URL", "").strip()

protected_names = {
    ".env",
    "database",
    "databases",
    "data",
    "instance",
    "uploads",
    "upload",
    "backups",
    "backup",
    "logs",
    "log",
    "storage",
    "media",
    "certificates",
    "certs",
    "keys",
    "node_modules",
    "mobile",
}
protected_suffixes = (".env", ".db", ".sqlite", ".sqlite3")


def fail(message):
    print(message)
    raise SystemExit(1)


def app_relative(src_rel):
    if src_rel.startswith("backend/"):
        return pathlib.Path(src_rel[len("backend/") :])
    return pathlib.Path(src_rel)


def validate_rel(src_rel):
    rel = pathlib.PurePosixPath(src_rel)
    parts = rel.parts
    if rel.is_absolute() or ".." in parts:
        fail(f"UNSAFE_PATH {src_rel}")
    if src_rel.startswith("baileys-api/") or src_rel == "baileys-api":
        fail(f"BAILEYS_BLOCKED {src_rel}")
    if "app-updates" in parts:
        fail(f"APP_UPDATES_BLOCKED {src_rel}")
    for part in parts:
        if part in protected_names:
            fail(f"PROTECTED_NAME_BLOCKED {src_rel}")
    if any(src_rel.endswith(suffix) for suffix in protected_suffixes):
        fail(f"PROTECTED_SUFFIX_BLOCKED {src_rel}")


def resolve_dest(src_rel):
    dest_rel = app_relative(src_rel)
    dest = (app_dir / dest_rel).resolve()
    try:
        dest.relative_to(app_dir)
    except ValueError:
        fail(f"DEST_OUTSIDE_APP {src_rel}")
    return dest_rel, dest


for src_rel in app_files:
    validate_rel(src_rel)
    src = pkg_dir / src_rel
    if not src.exists():
        fail(f"PACKAGE_ITEM_MISSING {src_rel}")
    resolve_dest(src_rel)

backup_file.parent.mkdir(parents=True, exist_ok=True)
manifest_path = pathlib.Path(str(backup_file) + ".manifest.txt")
backup_entries = []
for src_rel in app_files:
    dest_rel, dest = resolve_dest(src_rel)
    if dest.exists():
        backup_entries.append((dest, dest_rel))

if not backup_entries:
    fail("BACKUP_EMPTY")

with tarfile.open(backup_file, "w:gz") as tar:
    for dest, dest_rel in backup_entries:
        tar.add(dest, arcname=str(dest_rel).replace("\\", "/"), recursive=True)

with tarfile.open(backup_file, "r:gz") as tar:
    members = tar.getmembers()
    if not members:
        fail("BACKUP_TAR_EMPTY")
    manifest_path.write_text(
        "\n".join(member.name for member in members) + "\n",
        encoding="utf-8",
    )

print(f"APP_BACKUP_FILE={backup_file}")
print(f"APP_BACKUP_MANIFEST={manifest_path}")
print(f"APP_BACKUP_ENTRIES={len(members)}")
print("BAILEYS_PRODUCTION_PRESERVED_6_7_23")


def restore_backup():
    print("ROLLBACK_BEGIN")
    with tarfile.open(backup_file, "r:gz") as tar:
        for member in tar.getmembers():
            target = (app_dir / member.name).resolve()
            try:
                target.relative_to(app_dir)
            except ValueError:
                fail(f"ROLLBACK_TARGET_OUTSIDE_APP {member.name}")
        for src_rel in app_files:
            _dest_rel, dest = resolve_dest(src_rel)
            if dest.is_dir():
                shutil.rmtree(dest)
            elif dest.exists():
                dest.unlink()
        tar.extractall(app_dir)
    print("ROLLBACK_FILES_RESTORED")
    subprocess.run(restart_cmd, check=True)
    subprocess.run(["systemctl", "is-active", "menina"], check=True)
    print("ROLLBACK_SERVICE_ACTIVE")


try:
    for src_rel in app_files:
        src = pkg_dir / src_rel
        dest_rel, dest = resolve_dest(src_rel)
        if src.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        print(f"APPLIED {src_rel} -> {dest_rel}")

    subprocess.run(restart_cmd, check=True)
    subprocess.run(["systemctl", "is-active", "menina"], check=True)
    print("SERVICE_ACTIVE_AFTER_RESTART")

    if healthcheck_url:
        with urllib.request.urlopen(healthcheck_url, timeout=20) as response:
            print(f"HEALTHCHECK_STATUS={response.status}")
            if response.status >= 400:
                raise RuntimeError("HEALTHCHECK_HTTP_ERROR")
    else:
        print("HEALTHCHECK_SKIPPED_URL_NOT_CONFIGURED")

except Exception as exc:
    print(f"APPLY_FAILED={type(exc).__name__}: {exc}")
    try:
        restore_backup()
    except Exception as rollback_exc:
        print(f"ROLLBACK_FAILED={type(rollback_exc).__name__}: {rollback_exc}")
        raise SystemExit(3)
    raise SystemExit(2)

print("APPLY_OK")
PY
