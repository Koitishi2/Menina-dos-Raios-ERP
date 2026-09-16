import argparse
import ast
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "deploy" / "whatsapp_sellers_manifest.txt"
DEFAULT_OUTPUT = ROOT / "backups" / "deploy_packages" / "whatsapp_sellers"

PROTECTED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "uploads",
    "upload",
    "backups",
    "backup",
    "logs",
    "log",
    "storage",
    "media",
    "data",
    "database",
    "databases",
    "instance",
    "auth_info_baileys",
    "app-updates",
}
PROTECTED_SUFFIXES = (
    ".db",
    ".sqlite",
    ".sqlite3",
    ".env",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
)
SECRET_ASSIGN_RE = re.compile(
    r"(?i)^\s*(?:set\s+)?[\"']?[\w.-]*(password|passwd|secret|token|api_key)[\w.-]*\s*=\s*(.+?)\s*$"
)
KNOWN_MIGRATION_HASHES = {
    "backend/migrations/20260914_whatsapp_orders_up.sql": "9B0601BBCFB4C574DAC5F841514FA80A2E371D98F13093AE35C11D3749E69C2B",
    "backend/migrations/20260914_whatsapp_orders_down.sql": "BB9A33DB046C7FE724889D9C2A1AF3DF3730CD1B9D47D16A93601357E2E1B2FE",
    "backend/migrations/20260914_whatsapp_inbound_up.sql": "5E6FE3CEB3021155516D26E20D6251E1650551D693314DF72B8D9E1996ED6291",
    "backend/migrations/20260914_whatsapp_inbound_down.sql": "EAA81243C78BF47F5B6A77841235BC33915BB726610E955E948055BE5D3BC73C",
    "backend/migrations/20260916_sellers_up.sql": "D288CBA2DCD1CCEC736C62E1B444160561D8F549F002F703F25BAB479C4AB8D4",
    "backend/migrations/20260916_sellers_down.sql": "8037233A5D66BA327C976053EB97922B2DDE30AC244771DC8ADCAD732FBFD5FB",
}


class PackageError(RuntimeError):
    pass


def run(cmd, **kwargs):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True, **kwargs)


def parent_commit(commit):
    result = run(["git", "rev-parse", f"{commit}^"])
    return result.stdout.strip()


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_manifest(path):
    sections = {}
    current = None
    meta = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
        elif "=" in line:
            key, value = line.split("=", 1)
            meta[key.strip()] = value.strip()
    return meta, sections


def validate_relpath(rel):
    posix = PurePosixPath(rel)
    if posix.is_absolute() or ".." in posix.parts:
        raise PackageError(f"caminho inseguro no manifesto: {rel}")
    lowered = rel.lower()
    if lowered.startswith(("atualizar", "deploy/", "tests/")):
        raise PackageError(f"arquivo fora de runtime no pacote: {rel}")
    for part in posix.parts:
        if part in PROTECTED_DIRS:
            raise PackageError(f"diretorio protegido no pacote: {rel}")
    if lowered.endswith(PROTECTED_SUFFIXES):
        raise PackageError(f"arquivo protegido no pacote: {rel}")


def git_archive(commit, dest):
    run(["git", "cat-file", "-e", f"{commit}^{{commit}}"])
    archive = dest / "source.tar"
    with archive.open("wb") as f:
        subprocess.run(["git", "archive", "--format=tar", commit], cwd=ROOT, stdout=f, check=True)
    source = dest / "source"
    source.mkdir()
    with tarfile.open(archive, "r") as tar:
        tar.extractall(source)
    return source


def is_commit_published(commit, remote="origin"):
    refs = run(["git", "branch", "-r", "--contains", commit]).stdout
    return any(line.strip().startswith(f"{remote}/") for line in refs.splitlines())


def ensure_files(source, files):
    missing = [rel for rel in files if not (source / rel).exists()]
    if missing:
        raise PackageError("arquivos ausentes no commit: " + ", ".join(missing))


def iter_package_files(source, files):
    for rel in files:
        path = source / rel
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    yield child.relative_to(source).as_posix(), child
        else:
            yield rel, path


def scan_secrets(rel, path):
    if path.stat().st_size > 1024 * 1024:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    allowed_docs = rel in {"README.md", "deploy/whatsapp_sellers_manifest.txt"} or rel.endswith(".example.bat")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            if not allowed_docs:
                raise PackageError(f"possivel segredo em {rel}")
    for line in text.splitlines():
        match = SECRET_ASSIGN_RE.match(line)
        if not match:
            continue
        value = match.group(2).strip().rstrip(";")
        env_get_call = value
        if env_get_call.startswith("("):
            env_get_call = env_get_call[1:].strip()
        env_get_args = env_get_call.split(")", 1)[0]
        if (
            value in {'""', "''"}
            or value.startswith("{")
            or value.startswith("?")
            or (env_get_call.startswith("os.environ.get(") and "," not in env_get_args)
            or (env_get_call.startswith("os.getenv(") and "," not in env_get_args)
            or value.startswith("os.environ[")
            or value.startswith("request.headers.get(")
            or value.startswith("CURRENT_COMPANY.set(")
            or value.startswith("str(uuid.uuid4())")
            or value.startswith("cfg.get(")
        ):
            continue
        if not allowed_docs:
            raise PackageError(f"possivel segredo em {rel}")


def local_module_names(source):
    names = set()
    for py in (source / "backend").rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        rel = py.relative_to(source / "backend")
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts:
            names.add(".".join(parts))
            names.add(parts[-1])
    return names


def local_package_names(source):
    names = set()
    for init in (source / "backend").rglob("__init__.py"):
        if "__pycache__" in init.parts:
            continue
        rel = init.parent.relative_to(source / "backend")
        if rel.parts:
            names.add(".".join(rel.parts))
    return names


def validate_python_imports(source):
    modules = local_module_names(source)
    packages = local_package_names(source)
    missing = []
    for py in (source / "backend").rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        tree = ast.parse(py.read_text(encoding="utf-8-sig"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                first = node.module.split(".")[0]
                full = node.module
                if first in {"domains", "repositories", "routers", "services"} or full in modules:
                    if full not in modules and first not in modules:
                        missing.append(f"{py.relative_to(source)} -> {node.module}")
                    for alias in node.names:
                        candidate = f"{full}.{alias.name}"
                        if alias.name != "*" and first in {"domains", "repositories", "routers", "services"} and full in packages:
                            if candidate not in modules and alias.name not in modules:
                                missing.append(f"{py.relative_to(source)} -> {candidate}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    first = alias.name.split(".")[0]
                    if first in {"domains", "repositories", "routers", "services"} and first not in modules:
                        missing.append(f"{py.relative_to(source)} -> {alias.name}")
    if missing:
        raise PackageError("imports Python locais ausentes: " + ", ".join(sorted(set(missing))))


def validate_static_refs(source):
    html = source / "backend/static/index.html"
    if not html.exists():
        raise PackageError("index.html ausente")
    text = html.read_text(encoding="utf-8")
    refs = re.findall(r"""(?:src|href)=["']([^"']+\.(?:js|css))["']""", text)
    missing = []
    for ref in refs:
        if ref.startswith(("http://", "https://", "data:")):
            continue
        clean = ref.lstrip("/")
        candidates = [source / clean, source / "backend/static" / clean]
        if not any(path.exists() for path in candidates):
            missing.append(ref)
    if missing:
        raise PackageError("referencias JS/CSS ausentes no index.html: " + ", ".join(sorted(set(missing))))


def validate_node_refs(source):
    base = source / "baileys-api"
    for name in ("server.js", "inbound.js", "security.js", "package.json", "package-lock.json"):
        if not (base / name).exists():
            raise PackageError(f"Baileys runtime ausente: baileys-api/{name}")
    for script in ("server.js", "inbound.js", "security.js"):
        text = (base / script).read_text(encoding="utf-8")
        refs = re.findall(r"""require\(["'](\./[^"']+)["']\)""", text)
        for ref in refs:
            target = (base / ref)
            if not target.suffix:
                target = target.with_suffix(".js")
            if not target.exists():
                raise PackageError(f"require local ausente em baileys-api/{script}: {ref}")


def validate_migrations(source, sections):
    migrations = sections.get("migrations", [])
    order = sections.get("migration_order", [])
    rollback = sections.get("rollback_order", [])
    ensure_files(source, migrations + order + rollback)
    for rel, expected in KNOWN_MIGRATION_HASHES.items():
        path = source / rel
        if not path.exists():
            raise PackageError(f"migracao obrigatoria ausente: {rel}")
        actual = sha256(path)
        if actual != expected:
            raise PackageError(f"hash divergente para {rel}: {actual}")
    if order.index("backend/migrations/20260914_whatsapp_orders_up.sql") > order.index("backend/migrations/20260914_whatsapp_inbound_up.sql"):
        raise PackageError("ordem invalida: orders deve vir antes de inbound")
    if "backend/migrations/20260916_sellers_up.sql" not in order:
        raise PackageError("migracao sellers ausente da ordem")


def validate_package(source, sections):
    files = sections.get("runtime", []) + sections.get("migrations", [])
    if not files:
        raise PackageError("manifesto sem runtime/migrations")
    for rel in files:
        validate_relpath(rel)
    ensure_files(source, files)
    for rel, path in iter_package_files(source, files):
        validate_relpath(rel)
        scan_secrets(rel, path)
    validate_python_imports(source)
    validate_static_refs(source)
    validate_node_refs(source)
    validate_migrations(source, sections)
    return files


def write_package(source, files, output_dir, package_name):
    output_dir.mkdir(parents=True, exist_ok=True)
    package_path = output_dir / package_name
    manifest_path = output_dir / f"{package_path.stem}_MANIFEST.txt"
    checksums_path = output_dir / f"{package_path.stem}_SHA256SUMS.txt"
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, path in iter_package_files(source, files):
            zf.write(path, rel)
    package_hash = sha256(package_path)
    lines = []
    checksum_lines = [f"{package_hash}  {package_path.name}"]
    with zipfile.ZipFile(package_path) as zf:
        names = sorted(zf.namelist())
        for name in names:
            info = zf.getinfo(name)
            data = zf.read(name)
            h = hashlib.sha256(data).hexdigest().upper()
            lines.append(f"{name}\t{info.file_size}\t{h}")
            checksum_lines.append(f"{h}  {name}")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    checksums_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return package_path, package_hash, manifest_path, checksums_path, len(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gera pacote de deploy a partir de commit publicado.")
    parser.add_argument("--commit", default="47561e3359b77c78ce4d1a6fc0f43f790ace7f4b")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--require-published", action="store_true", default=True)
    parser.add_argument("--no-require-published", dest="require_published", action="store_false")
    args = parser.parse_args(argv)

    meta, sections = parse_manifest(args.manifest)
    if meta.get("version_commit") and meta["version_commit"] != args.commit:
        try:
            expected_parent = parent_commit(args.commit)
        except Exception:
            expected_parent = None
        if meta["version_commit"] != expected_parent:
            raise PackageError(
                f"commit diferente do manifesto: {meta['version_commit']}"
                f" (esperado {args.commit} ou seu pai {expected_parent})"
            )
    if args.require_published and not is_commit_published(args.commit):
        raise PackageError(f"commit nao publicado em remote conhecido: {args.commit}")

    package_name = meta.get("package_name") or f"bm_app_whatsapp_sellers_{args.commit[:7]}.zip"
    with tempfile.TemporaryDirectory(prefix="deploy_pkg_") as tmp:
        source = git_archive(args.commit, Path(tmp))
        files = validate_package(source, sections)
        package_path, package_hash, manifest_path, checksums_path, count = write_package(
            source, files, args.output_dir, package_name
        )

    print(f"PACKAGE={package_path}")
    print(f"PACKAGE_SHA256={package_hash}")
    print(f"MANIFEST={manifest_path}")
    print(f"CHECKSUMS={checksums_path}")
    print(f"FILE_COUNT={count}")
    print("REMOTE_ACCESS=NO")


if __name__ == "__main__":
    try:
        main()
    except (PackageError, subprocess.CalledProcessError) as exc:
        print(f"PACKAGE_BUILD_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
