"""Print the self-contained HTML kits to PDF with an isolated headless Chrome.

Usage: python3 tools/render_print.py print/kit-seed-42 print/fixed-edition
Requires Chrome or Chromium; the game itself has no browser dependency.
"""

import argparse
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def render(html: Path, browser: str) -> Path:
    pdf = html.with_suffix(".pdf").resolve()
    with tempfile.TemporaryDirectory(prefix="poisoned-dataset-print-") as profile:
        rendered = Path(profile) / "printed.pdf"
        result = subprocess.run([
            browser, "--headless", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update", "--disable-sync",
            "--no-pdf-header-footer", "--virtual-time-budget=2000",
            f"--user-data-dir={profile}", f"--print-to-pdf={rendered}", html.resolve().as_uri(),
        ], capture_output=True, text=True, timeout=120)
        if result.returncode or not rendered.exists() or not rendered.read_bytes().startswith(b"%PDF-"):
            raise RuntimeError(f"Could not print {html}: {result.stderr[-3000:]}")
        shutil.copyfile(rendered, pdf)
    print(f"Printed {pdf}", flush=True)
    return pdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", type=Path, nargs="+")
    parser.add_argument("--browser", help="Chrome/Chromium executable")
    args = parser.parse_args()
    browser = args.browser or next((p for p in (
        shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ) if p and Path(p).is_file()), None)
    if not browser:
        parser.error("Install Chrome/Chromium or pass --browser with its executable path.")
    html = [p for folder in args.folders for p in sorted(folder.glob("*.html"))]
    if not html:
        parser.error("No HTML files found in the supplied folders.")
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda p: render(p, browser), html))


if __name__ == "__main__":
    main()
