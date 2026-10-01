"""Create a clean zip of the project to share with teammates.

Usage, from the project folder:
    python scripts/make_zip.py        (Windows: py scripts/make_zip.py)

Writes Tcherly-TeachMate-<date>.zip next to the project folder. Everything that is
machine-specific or secret is left out: node_modules, Python environments, caches,
logs and .env files (API keys and login secrets). Each teammate recreates those
with `npm run setup` (see HOW_TO_RUN.md).
"""
import os
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP_FOLDER = "Tcherly-TeachMate"
SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".git", ".pytest_cache", ".cache", "coverage"}
SKIP_PATHS = {"client/build", "data/generated"}
SECRET_FILES = {".env", ".env.local", ".env.development.local", ".env.test.local", ".env.production.local", "settings.local.json"}
SKIP_SUFFIXES = {".log", ".pyc", ".zip"}


def files_to_share():
    for folder, dirs, files in os.walk(ROOT):
        rel_folder = Path(folder).relative_to(ROOT)
        # Prune in place so os.walk never descends into huge or private folders.
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and (rel_folder / d).as_posix() not in SKIP_PATHS)
        for name in sorted(files):
            rel = rel_folder / name
            if name in SECRET_FILES or rel.suffix in SKIP_SUFFIXES:
                continue
            yield rel


def main() -> None:
    out = ROOT.parent / f"{TOP_FOLDER}-{date.today().isoformat()}.zip"
    count = 0
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in files_to_share():
            archive.write(ROOT / rel, f"{TOP_FOLDER}/{rel.as_posix()}")
            count += 1

    with zipfile.ZipFile(out) as archive:
        leaked = [n for n in archive.namelist() if Path(n).name in SECRET_FILES or "/node_modules/" in n or "/.venv/" in n]
    if leaked:
        out.unlink()
        sys.exit(f"Refusing to create the zip: it would contain private or machine-specific files: {leaked[:5]}")

    print(f"Created {out}")
    print(f"{count} files, {out.stat().st_size / 1_000_000:.1f} MB (no node_modules, no .venv, no .env secrets)")


if __name__ == "__main__":
    main()
