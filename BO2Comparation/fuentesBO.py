#compara fuentes de reportes pro vs qa para comprobar si los cambios del selector de fuente elminado no haya afectado el tamaño de fuente


import os
import re
import unicodedata
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# ————— Credenciales —————
CREDENTIALS = {
    "QA": {
        "base": "https://backoffice-v2.qa.wcbackoffice.com",
        "user": "mcastro",
        "pass": "N3wP@ssw0rd2024"
    },
    "Andes": {
        "base": "https://backoffice-v2-wyc.andes-system.com",
        "user": "administrador_qa",
        "pass": "QAuser*2025"
    }
}

# ————— Rutas de reportes —————
REPORT_PATHS = [
    "/reports/player-balance",
    "/reports/player-list",
    "/reports/balance-skin",
    "/reports/registered-players",
    "/reports/blacklist",
    "/reports/automatic-charge",
    "/reports/notification-list",
    "/reports/player-online",
    "/reports/weekend-bonus",
    "/reports/player-conciliation",
    "/reports/player-charge-summary",
    "/reports/liquidation-seller",
    "/reports/pending-revocation",
]

HTML_REPORT_PATH = "font_sizes_comparison_report.html"
ELEMENTS_COMPARED = ["body", "th", "td"]

def login(page, base_url, username, password):
    page.goto(base_url, wait_until="networkidle")
    page.fill("//input[@placeholder='Usuario']", username)
    page.fill("//input[@placeholder='Contraseña']", password)
    page.click("//input[@value='Ingresar']")
    page.wait_for_load_state("networkidle")

def extract_font_sizes(page):
    selector_list = ",".join(f"'{e}'" for e in ELEMENTS_COMPARED)
    js = f"""
    () => {{
      const els = Array.from(document.querySelectorAll([{selector_list}]));
      const style = window.getComputedStyle;
      return Array.from(new Set(els.map(e => style(e).fontSize)))
                  .sort((a, b) => parseFloat(a) - parseFloat(b));
    }}
    """
    return page.evaluate(js)

def generate_html_report(results, output_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = ""
    for path in REPORT_PATHS:
        qa = ", ".join(results["QA"][path])
        an = ", ".join(results["Andes"][path])
        rows += f"""
      <tr>
        <td>{path}</td>
        <td>{qa}</td>
        <td>{an}</td>
      </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Comparativo de Tamaños de Fuente</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    h1 {{ margin-bottom: 0; }}
    .meta, .details {{ margin-top: 8px; color: #555; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #f4f4f4; }}
    ul {{ margin: 4px 0 8px 20px; }}
  </style>
</head>
<body>
  <h1>Comparativo de Tamaños de Fuente</h1>
  <p class="meta">Fecha de generación: {timestamp}</p>
  <div class="details">
    <p><strong>Entornos comparados:</strong></p>
    <ul>
      <li><strong>QA:</strong> {CREDENTIALS["QA"]["base"]} (usuario: {CREDENTIALS["QA"]["user"]})</li>
      <li><strong>Andes:</strong> {CREDENTIALS["Andes"]["base"]} (usuario: {CREDENTIALS["Andes"]["user"]})</li>
    </ul>
    <p><strong>Report Paths:</strong></p>
    <ul>
      {''.join(f'<li>{p}</li>' for p in REPORT_PATHS)}
    </ul>
    <p><strong>Elementos comparados:</strong> {', '.join(ELEMENTS_COMPARED)}</p>
  </div>
  <table>
    <thead>
      <tr>
        <th>Ruta</th>
        <th>QA (px)</th>
        <th>Andes (px)</th>
      </tr>
    </thead>
    <tbody>
    {rows}
    </tbody>
  </table>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Reporte HTML generado: {output_path}")

def main():
    results = {"QA": {}, "Andes": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for env, cfg in CREDENTIALS.items():
            ctx = browser.new_context()
            page = ctx.new_page()
            login(page, cfg["base"], cfg["user"], cfg["pass"])
            for path in REPORT_PATHS:
                page.goto(cfg["base"] + path, wait_until="networkidle")
                page.wait_for_timeout(500)
                results[env][path] = extract_font_sizes(page)
            ctx.close()
        browser.close()
    generate_html_report(results, HTML_REPORT_PATH)

if __name__ == "__main__":
    main()
