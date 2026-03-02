from pathlib import Path
import shutil

dirs = [".pytest_cache", ".ruff_cache", ".mypy_cache"]

for d in dirs:
    if Path(d).exists():
        shutil.rmtree(d)

for p in Path(".").rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)

print("Cache directories cleaned.")
