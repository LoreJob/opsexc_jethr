"""Build the GitHub Pages app from the Flask UI and the shared Python converter."""

from hashlib import sha256
from pathlib import Path
from shutil import copy2, copytree, rmtree
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
sys.path.insert(0, str(ROOT))

from app import app


def main() -> None:
    version_hash = sha256()
    for path in (
        ROOT / "converter.py",
        ROOT / "templates" / "index.html",
        ROOT / "static" / "app.js",
        ROOT / "static" / "pyodide-worker.js",
        ROOT / "static" / "styles.css",
        ROOT / "Kit Candidato" / "config" / "Lista_Dipendenti.csv",
        ROOT / "Kit Candidato" / "config" / "Codici_Welfare_Voci_Payroll.csv",
    ):
        version_hash.update(path.read_bytes())
    version = version_hash.hexdigest()[:12]

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
    page = page.replace(marker, f'<script>window.CONVERSION_MODE = "browser"; window.APP_VERSION = "{version}";</script>\n  ' + marker)
    for name in ("favicon.svg", "styles.css", "app.js", "jet-hr-logo.svg"):
        page = page.replace(f'"static/{name}"', f'"static/{name}?v={version}"')
    (OUTPUT / "index.html").write_text(page, encoding="utf-8")
    (OUTPUT / ".nojekyll").touch()
    copytree(ROOT / "static", OUTPUT / "static")
    copy2(ROOT / "converter.py", OUTPUT / "converter.py")
    (OUTPUT / "config").mkdir()
    for name in ("Lista_Dipendenti.csv", "Codici_Welfare_Voci_Payroll.csv"):
        copy2(ROOT / "Kit Candidato" / "config" / name, OUTPUT / "config" / name)


if __name__ == "__main__":
    main()
