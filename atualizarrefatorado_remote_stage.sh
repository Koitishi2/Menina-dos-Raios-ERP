set -eu

cd "$REMOTE_RUN_DIR"
printf '%s  %s\n' "$EXPECTED_SHA" "$ZIP_NAME" > SHA256SUMS
$REMOTE_HASH_TOOL -c SHA256SUMS

mkdir pkg
$REMOTE_UNZIP_TOOL "$ZIP_NAME" pkg

test -f "$REMOTE_RUN_DIR/pkg/backend/app.py"
test -f "$REMOTE_RUN_DIR/pkg/backend/requirements.txt"
test -f "$REMOTE_RUN_DIR/pkg/backend/static/index.html"

cd "$REMOTE_RUN_DIR/pkg"
python3 <<'PY'
import os
import sys

files = sorted(
    "./" + os.path.relpath(os.path.join(root, name), ".")
    for root, _dirs, names in os.walk(".")
    for name in names
)
blocked = [
    path
    for path in files
    if path == "./.env"
    or path.endswith(".env")
    or path.endswith(".db")
    or path.endswith(".sqlite")
    or path.endswith(".sqlite3")
    or path[:10] == "./uploads/"
    or path[:10] == "./backups/"
    or path[:7] == "./logs/"
    or path[:10] == "./storage/"
    or path[:8] == "./media/"
    or path[:29] == "./backend/static/app-updates/"
]

for path in files:
    print(path)

if blocked:
    print("ERRO_ITEM_PROTEGIDO_NO_ZIP")
    for path in blocked:
        print(path)
    sys.exit(3)

print("STAGING_OK")
PY

echo "BAILEYS_STAGING_BEGIN"
echo "BAILEYS_REPOSITORY=https://github.com/WhiskeySockets/Baileys"
echo "BAILEYS_INSTALL_METHOD=npm install --save-exact @whiskeysockets/baileys@github:WhiskeySockets/Baileys"
echo "BAILEYS_INSTALL_TIME_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "NODE_VERSION=$(node --version)"
echo "NPM_VERSION=$(npm --version)"
node -e "const major=Number(process.versions.node.split('.')[0]); if(major < 20){ console.error('NODE_VERSION_LT_20'); process.exit(20) }"

test -d "$REMOTE_BAILEYS_DIR"
test -f "$REMOTE_BAILEYS_DIR/package.json"
if test -f "$REMOTE_BAILEYS_DIR/package-lock.json"; then
  echo "BAILEYS_LOCKFILE_PRESENT"
else
  echo "BAILEYS_LOCKFILE_NOT_FOUND"
fi
if test -f "$REMOTE_BAILEYS_DIR/.env"; then
  echo "BAILEYS_ENV_PRESENT"
else
  echo "BAILEYS_ENV_NOT_FOUND"
fi
if test -d "$REMOTE_BAILEYS_DIR/auth_info_baileys"; then
  echo "BAILEYS_AUTH_DIR_PRESENT"
else
  echo "BAILEYS_AUTH_DIR_NOT_FOUND"
fi

cp -a "$REMOTE_BAILEYS_DIR" "$REMOTE_RUN_DIR/baileys_work"
cp -a "$REMOTE_RUN_DIR/pkg/baileys-api/package.json" "$REMOTE_RUN_DIR/baileys_work/package.json"
cp -a "$REMOTE_RUN_DIR/pkg/baileys-api/server.js" "$REMOTE_RUN_DIR/baileys_work/server.js"

cd "$REMOTE_RUN_DIR/baileys_work"
node -e "const pkg=require('./package.json'); const deps=pkg.dependencies||{}; console.log('BAILEYS_BEFORE='+JSON.stringify(deps['@whiskeysockets/baileys']||null));"
cp -a package.json package.json.before-github-baileys
if test -f package-lock.json; then
  cp -a package-lock.json package-lock.json.before-github-baileys
fi
python3 <<'PY'
import json
import pathlib
import shutil

pkg_path = pathlib.Path("package.json")
pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
    deps = pkg.get(section)
    if isinstance(deps, dict):
        deps.pop("@whiskeysockets/baileys", None)
pkg_path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

lock_path = pathlib.Path("package-lock.json")
if lock_path.exists():
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    packages = lock.get("packages")
    if isinstance(packages, dict):
        packages.pop("node_modules/@whiskeysockets/baileys", None)
        root = packages.get("")
        if isinstance(root, dict):
            for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                deps = root.get(section)
                if isinstance(deps, dict):
                    deps.pop("@whiskeysockets/baileys", None)
    deps = lock.get("dependencies")
    if isinstance(deps, dict):
        deps.pop("@whiskeysockets/baileys", None)
    lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

target = pathlib.Path("node_modules") / "@whiskeysockets" / "baileys"
if target.exists():
    shutil.rmtree(target)
PY
npm install --save-exact @whiskeysockets/baileys@github:WhiskeySockets/Baileys
node -e "const pkg=require('./package.json'); const deps=pkg.dependencies||{}; console.log('BAILEYS_AFTER='+JSON.stringify(deps['@whiskeysockets/baileys']||null));"
node -e "const lock=require('./package-lock.json'); const pkgs=lock.packages||{}; const dep=pkgs['node_modules/@whiskeysockets/baileys']||{}; console.log('BAILEYS_LOCK_VERSION='+JSON.stringify(dep.version||null)); console.log('BAILEYS_LOCK_RESOLVED='+JSON.stringify(dep.resolved||null));"
node --check server.js
node -e "require.resolve('@whiskeysockets/baileys'); console.log('BAILEYS_REQUIRE_OK')"
git_commit="$(node -e "const lock=require('./package-lock.json'); const dep=(lock.packages||{})['node_modules/@whiskeysockets/baileys']||{}; const resolved=String(dep.resolved||''); const pkg=require('./package.json'); const spec=String((pkg.dependencies||{})['@whiskeysockets/baileys']||''); const text=resolved+' '+spec; const m=text.match(/[?#]([0-9a-f]{40})$/i)||text.match(/commit=([0-9a-f]{40})/i)||text.match(/#([0-9a-f]{40})/i); console.log(m?m[1]:'UNKNOWN')")"
origin_ok="$(node -e "const lock=require('./package-lock.json'); const dep=(lock.packages||{})['node_modules/@whiskeysockets/baileys']||{}; const resolved=String(dep.resolved||''); const pkg=require('./package.json'); const spec=String((pkg.dependencies||{})['@whiskeysockets/baileys']||''); const ok=/github\\.com[:/]WhiskeySockets\\/Baileys/i.test(resolved)||/github:WhiskeySockets\\/Baileys/i.test(spec)||/github\\.com[:/]WhiskeySockets\\/Baileys/i.test(spec); console.log(ok?'yes':'no')")"
if test "$origin_ok" != "yes" || test "$git_commit" = "UNKNOWN"; then
  echo "BAILEYS_GITHUB_ORIGIN_NOT_PROVEN"
  node -e "const lock=require('./package-lock.json'); const dep=(lock.packages||{})['node_modules/@whiskeysockets/baileys']||{}; const pkg=require('./package.json'); console.log('package_dependency='+String((pkg.dependencies||{})['@whiskeysockets/baileys']||'')); console.log('lock_resolved='+String(dep.resolved||''));"
  exit 42
fi
{
  echo "repository=https://github.com/WhiskeySockets/Baileys"
  echo "install_method=npm install --save-exact @whiskeysockets/baileys@github:WhiskeySockets/Baileys"
  echo "install_time_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "node_version=$(node --version)"
  echo "npm_version=$(npm --version)"
  echo "baileys_commit=$git_commit"
  echo "origin_ok=$origin_ok"
  sha256sum package.json package-lock.json
  node -e "const pkg=require('./package.json'); const deps=pkg.dependencies||{}; console.log('package_dependency='+String(deps['@whiskeysockets/baileys']||''))"
  node -e "const lock=require('./package-lock.json'); const dep=(lock.packages||{})['node_modules/@whiskeysockets/baileys']||{}; console.log('lock_version='+String(dep.version||'')); console.log('lock_resolved='+String(dep.resolved||''));"
} > "$REMOTE_RUN_DIR/baileys_staging_manifest.txt"
cat "$REMOTE_RUN_DIR/baileys_staging_manifest.txt"
echo "BAILEYS_STAGING_OK"
