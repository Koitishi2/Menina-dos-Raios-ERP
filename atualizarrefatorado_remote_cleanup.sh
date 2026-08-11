set -eu

python3 <<'PY'
import os
import pathlib
import shutil
import sys

run_dir = pathlib.Path(os.environ["RUN_DIR"])
base_dir = pathlib.Path(os.environ["BASE_DIR"])
prefix = os.environ["PREFIX"]

ok = run_dir.parent == base_dir and run_dir.name[: len(prefix)] == prefix
if ok and run_dir.exists():
    shutil.rmtree(run_dir)

print("STAGING_CLEANUP_OK" if ok else "STAGING_CLEANUP_BLOCKED")
sys.exit(0 if ok else 4)
PY
