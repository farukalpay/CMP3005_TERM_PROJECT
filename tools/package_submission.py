"""Package source and saved evidence; never runs experiments or uploads files."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables/CMP3005_Code_FarukAlpay_2267273.zip"
EXCLUDE_DIRS = {".git", ".venv", ".local-backup", "archive", "tmp", "__pycache__"}
DEBRIS = {".aux", ".bbl", ".blg", ".fls", ".log", ".nav", ".out", ".snm", ".toc", ".vrb", ".pyc", ".o", ".zip"}


def include(path):
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts) or path.name == ".DS_Store":
        return False
    if rel.parts[:2] in (("solver", "bin"), ("solver", "build")):
        return False
    if path.suffix in DEBRIS or path.name.endswith((".fdb_latexmk", ".synctex.gz")):
        return False
    if rel.as_posix() in ("report/research.pdf", "slides/slides.pdf"):
        return False
    return True


def main():
    report = ROOT / "deliverables/CMP3005_Report_FarukAlpay_2267273.pdf"
    if not report.is_file():
        raise SystemExit("Build the current report with make report first.")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and include(p))
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
    print(f"Created {OUTPUT.name}: {len(files)} files, {OUTPUT.stat().st_size / 1024**2:.1f} MiB")


if __name__ == "__main__":
    main()
