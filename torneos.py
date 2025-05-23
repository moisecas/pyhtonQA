# validar sección torneos 

import os
import html
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuración ---
URL = "https://skin2-latamwin.qa.andes-system.com/"

VIEWPORTS = [
    ("desktop",   1360, 768),
    ("mobile-sm",  375, 667),
    ("mobile-md",  414, 896),
]

# Elementos a inspeccionar: (clave para informe, selector)
ELEMENTS = [
    ("sección_torneos",  "div[data-testid='swiper-section-middle-custom-id']"),
    ("titulo_torneos",   "div[data-testid='swiper-section-middle-custom-id'] >> text=Torneos"),
    ("btn_anterior",     "button[data-testid='swiper-navigation-custom-prev-button-id']"),
    ("btn_siguiente",    "button[data-testid='swiper-navigation-custom-next-button-id']"),
    ("carta_activa",     "div.slick-slide.slick-current div[data-testid^='tournament-card-']"),
    ("btn_unirme",       "button[data-testid='tournament-join-button-test-id']"),
]

REPORT_DIR = "reports/tournaments"
os.makedirs(REPORT_DIR, exist_ok=True)


def main():
    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp_name, vp_w, vp_h in VIEWPORTS:
            page = browser.new_page()
            page.set_viewport_size({"width": vp_w, "height": vp_h})
            page.goto(URL, wait_until="networkidle")

            for key, selector in ELEMENTS:
                # localizador
                locator = page.locator(selector).first

                # esperar un poco si es necesario
                try:
                    locator.wait_for(state="visible", timeout=5000)
                except:
                    print(f"⚠️ [{vp_name}] Elemento «{key}» no encontrado o no visible.")
                    continue

                # bounding box
                box = locator.bounding_box()
                if not box:
                    print(f"⚠️ [{vp_name}] No se pudo obtener bounding box de «{key}».")
                    continue

                w = int(box["width"])
                h = int(box["height"])

                # captura de pantalla
                img_path = os.path.join(REPORT_DIR, f"{vp_name}_{key}.png")
                locator.screenshot(path=img_path)

                rows.append({
                    "viewport": vp_name,
                    "element": key,
                    "size": f"{w}×{h}",
                    "img": os.path.basename(img_path)
                })

            page.close()

        browser.close()

    # --- Generar HTML ---
    html_rows = ""
    for r in rows:
        html_rows += f"""
      <tr>
        <td>{html.escape(r['viewport'])}</td>
        <td>{html.escape(r['element'])}</td>
        <td style="text-align:center">{html.escape(r['size'])}</td>
        <td><img src="{html.escape(r['img'])}" style="max-width:200px; border:1px solid #ccc"></td>
      </tr>
    """

    if not html_rows:
        html_rows = """
      <tr>
        <td colspan="4" style="text-align:center">No se capturó ningún elemento.</td>
      </tr>
    """

    report_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte de Torneos - {URL}</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; }}
    th {{ background: #f4f4f4; }}
    img {{ display: block; margin: 4px 0; }}
  </style>
</head>
<body>
  <h1>Reporte de “Torneos”</h1>
  <p><strong>URL evaluada:</strong> {URL}</p>
  <p><strong>Fecha generación:</strong> {timestamp}</p>
  <table>
    <thead>
      <tr>
        <th>Viewport</th>
        <th>Elemento</th>
        <th>W×H (px)</th>
        <th>Captura</th>
      </tr>
    </thead>
    <tbody>
{html_rows}
    </tbody>
  </table>
</body>
</html>
"""

    report_path = os.path.join(REPORT_DIR, "tournaments_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    print(f"✅ Reporte generado: {report_path}")


if __name__ == "__main__":
    main()
