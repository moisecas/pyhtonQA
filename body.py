# body_styles_report.py

from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import html as hm

def run_body_styles_check():
    # 1) Configuración general
    url = "https://skin2-latamwin.qa.andes-system.com/"
    # Lista de viewports a probar
    viewports = [
        ("Desktop",   1360, 3357),
        ("Mobile XS", 360,  640),
        ("Mobile SM", 375,  812),
        ("Mobile LG", 414,  896),
    ]

    # Crear carpeta de reportes
    os.makedirs("reports/screenshots", exist_ok=True)

    # Almacenar resultados
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for name, w, h in viewports:
            page = browser.new_page()
            page.set_viewport_size({"width": w, "height": h})

            # Navegar
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

            # Extraer propiedades de <body>
            props = page.evaluate(r"""
                () => {
                    const cs = getComputedStyle(document.body);
                    return {
                        bgImage:    cs.getPropertyValue('background-image'),
                        bgColor:    cs.getPropertyValue('background-color'),
                        bgRepeat:   cs.getPropertyValue('background-repeat'),
                        bgSize:     cs.getPropertyValue('background-size'),
                        bgPosition: cs.getPropertyValue('background-position'),
                        width:      document.body.getBoundingClientRect().width,
                        height:     document.body.getBoundingClientRect().height
                    };
                }
            """)

            # Captura de pantalla
            shot_name = f"{name.replace(' ','_').lower()}_body.png"
            shot_path = os.path.join("reports/screenshots", shot_name)
            page.screenshot(path=shot_path, full_page=True)
            page.close()

            # Guardar resultado
            results.append({
                "resolution": name,
                **props,
                "screenshot": shot_name
            })

        browser.close()

    # 2) Generar reporte HTML
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Construir filas de la tabla
    rows = []
    for r in results:
        rows.append(f"""
      <tr>
        <td>{hm.escape(r["resolution"])}</td>
        <td>{hm.escape(r["bgImage"])}</td>
        <td>{hm.escape(r["bgColor"])}</td>
        <td>{hm.escape(r["bgRepeat"])}</td>
        <td>{hm.escape(r["bgSize"])}</td>
        <td>{hm.escape(r["bgPosition"])}</td>
        <td>{r["width"]:.2f}</td>
        <td>{r["height"]:.2f}</td>
        <td><a href="screenshots/{r["screenshot"]}">{r["screenshot"]}</a></td>
      </tr>
    """)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte Body Styles Multiresolución</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; vertical-align: top; }}
    th {{ background: #f4f4f4; }}
    a {{ color: #0066cc; text-decoration: none; }}
  </style>
</head>
<body>
  <h1>Reporte Body Styles Multiresolución</h1>
  <p><strong>URL evaluada:</strong> {url}</p>
  <p><strong>Generado:</strong> {now}</p>
  <table>
    <thead>
      <tr>
        <th>Resolución</th>
        <th>background-image</th>
        <th>background-color</th>
        <th>background-repeat</th>
        <th>background-size</th>
        <th>background-position</th>
        <th>body width (px)</th>
        <th>body height (px)</th>
        <th>Screenshot</th>
      </tr>
    </thead>
    <tbody>
{''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""

    report_path = os.path.join("reports", "body_styles_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Reporte HTML multiresolución generado: {report_path}")

if __name__ == "__main__":
    run_body_styles_check() 
