"""Cria um ZIP de entrega sem arquivos temporarios ou binarios locais."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "build" / "packages" / "n_rainhas_tecnico.zip"
INCLUDE = [ROOT / "README.md"]
for folder in ("src", "scripts", "tests", "data"):
    INCLUDE.extend(
        path for path in (ROOT / folder).rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix.lower() != ".pyc"
    )

DEST.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(DEST, "w", ZIP_DEFLATED) as archive:
    for path in sorted(INCLUDE):
        if path == DEST:
            continue
        archive.write(path, path.relative_to(ROOT))
print(f"Pacote: {DEST}")
