#!/usr/bin/env python3
# comparar ui con excel archivos de hashes críticos 

import os
import re
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import pandas as pd

# ————— Setup logging —————
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ————— Carga de .env —————
project_root = Path(__file__).parent
load_dotenv(project_root.parent / ".env")

# ————— Hashes conocidos (de Excel), hardcodeados —————
# Nota: si quieres cargar desde un CSV/JSON externo, puedes reemplazar este bloque.
HARDCODED_HASHES = [
   
]

# ————— Parsers y selectores —————
SEL_USER_FIELD = "input[placeholder='Usuario']"
SEL_PASS_FIELD = "input[placeholder='Contraseña']"
SEL_LOGIN_BTN  = "input[value='Ingresar']"
SEL_TABLE_ROW  = "table tbody tr"
SEL_NEXT_BTN   = "//a[normalize-space()='Siguiente']"
HASH_COL_INDEX = 2  # columna 0-based donde está el hash en la tabla web

# ————— Argumentos de línea de comandos —————
def parse_args():
    p = argparse.ArgumentParser(description="Compara hashes hardcodeados vs web")
    p.add_argument("--base-url", default="https://backoffice-v2.qa.wcbackoffice.com",
                   help="URL base del BackOffice")
    p.add_argument("--user", default="efermin", help="Usuario para login")
    p.add_argument("--excel-hashes", type=Path,
                   help="(Opcional) Ruta a Excel/CSV con hashes en lugar de hardcodear",
                   default=None)
    p.add_argument("--output-html", type=Path,
                   default=project_root/"reporte_comparacion.html",
                   help="Ruta donde guardar el HTML de reporte")
    return p.parse_args()

def get_web_hashes(base_url: str, user: str, password: str) -> set[str]:
    """Abre Playwright, hace login y extrae hashes de dos páginas."""
    logging.info("Lanzando Playwright y extrayendo hashes de la web...")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx     = browser.new_context()
            page    = ctx.new_page()

            # Login
            page.goto(base_url, wait_until="networkidle")
            page.fill(SEL_USER_FIELD, user)
            page.fill(SEL_PASS_FIELD, password)
            page.click(SEL_LOGIN_BTN)
            page.wait_for_load_state("networkidle")

            # Página 1
            page.goto(f"{base_url}/admin/critical-files", wait_until="networkidle")
            hashes = extract_hashes(page)

            # Página 2
            page.click(SEL_NEXT_BTN)
            page.wait_for_selector(SEL_TABLE_ROW, timeout=10_000)
            hashes += extract_hashes(page)

            ctx.close()
            browser.close()
    except PWTimeoutError as e:
        logging.error("Timeout extrayendo datos de la web: %s", e)
        sys.exit(2)

    unique = set(hashes)
    logging.info("Encontrados %d hashes únicos en la web.", len(unique))
    return unique

def extract_hashes(page, col_index: int = HASH_COL_INDEX) -> list[str]:
    lst = []
    for row in page.query_selector_all(SEL_TABLE_ROW):
        cells = row.query_selector_all("td")
        if len(cells) > col_index:
            lst.append(cells[col_index].inner_text().strip())
    return lst

def load_excel_hashes(path: Path) -> list[str]:
    """Si se provee un Excel o CSV, carga su columna de hash."""
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str)
    df = df.dropna().astype(str).applymap(str.strip)
    # Buscar la columna que contenga 'hash'
    cols = [c for c in df.columns if "hash" in c.lower()]
    if not cols:
        raise ValueError(f"No encontré columna con 'hash' en {path.name}")
    return df[cols[0]].tolist()

def generate_html_report(web: set[str],
                         excel: set[str],
                         duplicates: int,
                         total_excel: int,
                         out: Path) -> None:
    """Genera un HTML con la comparación."""
    from datetime import datetime
    df = pd.DataFrame({
        "hash": sorted(excel),
        "estado": ["Encontrado" if h in web else "No encontrado" for h in sorted(excel)]
    })
    html_table = df.to_html(index=False, border=1, justify="center")
    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Reporte de Hashes</title>
<style>
  body{{font-family:Arial,sans-serif;margin:2em;}}
  table{{border-collapse:collapse;width:100%;}}
  th,td{{padding:8px;text-align:center;border:1px solid #ccc;}}
  th{{background-color:#f2f2f2;}}
  .Encontrado{{background-color:#d4edda;}}
  .No\\ encontrado{{background-color:#f8d7da;}}
</style></head>
<body>
  <h1>📊 Reporte de Comparación de Hashes</h1>
  <p>Generado: {datetime.now().isoformat()}</p>
  <ul>
    <li>Hashes extraídos de la web: <strong>{len(web)}</strong></li>
    <li>Total en Excel (bruto): <strong>{total_excel}</strong></li>
    <li>Únicos en Excel: <strong>{len(excel)}</strong></li>
    <li>Duplicados en Excel: <strong>{duplicates}</strong></li>
    <li>No encontrados: <strong>{len(excel - web)}</strong></li>
  </ul>
  {html_table}
</body>
</html>"""
    out.write_text(html, encoding="utf-8")
    logging.info("Reporte HTML guardado en %s", out)

def main():
    args = parse_args()

    # 1) Extraer hashes web
    pw_pass = os.getenv("EFERMIN_PASS")
    if not pw_pass:
        logging.error("No está definida la variable EFERMIN_PASS en .env")
        sys.exit(1)
    web_hashes = get_web_hashes(args.base_url, args.user, pw_pass)

    # 2) Cargar o tomar hardcodeados
    if args.excel_hashes:
        raw_list = load_excel_hashes(args.excel_hashes)
        logging.info("Cargados %d hashes desde %s", len(raw_list), args.excel_hashes.name)
    else:
        raw_list = HARDCODED_HASHES.copy()
        logging.info("Usando lista hardcodeada con %d entradas", len(raw_list))

    total_excel = len(raw_list)
    unique_excel = set(raw_list)
    duplicates = total_excel - len(unique_excel)
    logging.info("Excel: %d totales, %d únicos, %d duplicados", total_excel, len(unique_excel), duplicates)

    # 3) Generar reporte
    generate_html_report(web_hashes, unique_excel, duplicates, total_excel, args.output_html)

if __name__ == "__main__":
    main()
