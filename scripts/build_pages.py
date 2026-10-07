"""Build the GitHub Pages app from the Flask UI and the shared Python converter."""

from pathlib import Path
from shutil import copy2, copytree, rmtree
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
sys.path.insert(0, str(ROOT))

from app import app


def main() -> None:
    if OUTPUT.exists():
        rmtree(OUTPUT)
    OUTPUT.mkdir()
    with app.test_client() as client:
        page = client.get("/").get_data(as_text=True)
    page = page.replace('href="/static/', 'href="static/')
    page = page.replace('src="/static/', 'src="static/')
    marker = '<script src="static/app.js" defer></script>'
    if marker not in page:
        raise RuntimeError("Impossibile trovare lo script principale nella pagina.")
    page = page.replace(marker, '<script>window.CONVERSION_MODE = "browser";</script>\n  ' + marker)
    (OUTPUT / "index.html").write_text(page, encoding="utf-8")
    (OUTPUT / ".nojekyll").touch()
    copytree(ROOT / "static", OUTPUT / "static")
    copy2(ROOT / "converter.py", OUTPUT / "converter.py")
    (OUTPUT / "config").mkdir()
    for name in ("Lista_Dipendenti.csv", "Codici_Welfare_Voci_Payroll.csv"):
        copy2(ROOT / "Kit Candidato" / "config" / name, OUTPUT / "config" / name)


if __name__ == "__main__":
    main()
