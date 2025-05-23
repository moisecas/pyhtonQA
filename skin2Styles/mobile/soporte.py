#skin2 soporte 

from playwright.sync_api import sync_playwright
from datetime import datetime
import html as hm

# Credenciales y URLs
USER = "TEST_GM2"
PASSWORD = "Cc12345678@@"
LOGIN_URL = "https://skin2-latamwin.qa.andes-system.com/"
TARGET_URL = "https://skin2-latamwin.qa.andes-system.com/support/contact"

# Lista de viewports móviles a evaluar
VIEWPORTS = [
    {"label": "360×640", "width": 360, "height": 640},
    {"label": "375×667", "width": 375, "height": 667},
    {"label": "414×896", "width": 414, "height": 896},
]

def extract_per_viewport():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for vp in VIEWPORTS:
            page = browser.new_page()
            # Ajustar viewport
            page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            # 1) Login
            page.goto(LOGIN_URL)
            page.click("button:has-text('Ingresar')")
            page.fill("input[placeholder='Usuario']", USER)
            page.fill("input[placeholder='Contraseña']", PASSWORD)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            # 2) Cerrar modal si aparece
            try:
                page.click(
                    "xpath=//header[@class='flex items-baseline justify-between gap-5 py-5']//*[name()='svg']",
                    timeout=3000
                )
            except:
                pass
            # 3) Ir a Support Contact
            page.goto(TARGET_URL)
            page.wait_for_load_state("networkidle")
            # 4) Extraer elementos con texto y fontFamily
            items = page.evaluate("""
                () => {
                    const out = [];
                    document.querySelectorAll('*').forEach(el => {
                        let txt = el.textContent.trim();
                        if (!txt && el.placeholder) txt = el.placeholder;
                        if (!txt) return;
                        if (txt.length > 100) txt = txt.slice(0,100) + '…';
                        const font = window.getComputedStyle(el).fontFamily;
                        out.push({ tag: el.tagName.toLowerCase(), content: txt, font });
                    });
                    return out;
                }
            """)
            results.append({"viewport": vp["label"], "items": items})
            page.close()
        browser.close()
    return results

def generate_report_per_viewport(data, filename="support_contact_mobile_report.html"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte Fuentes por Viewport</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    h2 {{ margin-top: 40px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; vertical-align: top; }}
    th {{ background: #f4f4f4; }}
    td.content {{ max-width: 300px; word-wrap: break-word; }}
    code {{ background: #eee; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>Reporte Detallado de Fuentes</h1>
  <p><strong>URL evaluada:</strong> {TARGET_URL}</p>
  <p><strong>Fecha generación:</strong> {now}</p>
"""
    for vp_data in data:
        html += f"  <h2>Viewport {vp_data['viewport']}</h2>\n"
        html += """  <table>
    <thead>
      <tr><th>Etiqueta</th><th>Contenido</th><th>Font Family</th></tr>
    </thead>
    <tbody>
"""
        for it in vp_data["items"]:
            tag = hm.escape(it["tag"])
            content = hm.escape(it["content"])
            font = hm.escape(it["font"])
            html += (
                f"      <tr>\n"
                f"        <td><code>{tag}</code></td>\n"
                f"        <td class='content'>{content}</td>\n"
                f"        <td><code>{font}</code></td>\n"
                f"      </tr>\n"
            )
        html += "    </tbody>\n  </table>\n"
    html += "</body>\n</html>"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Reporte generado: {filename}")

if __name__ == "__main__":
    data = extract_per_viewport()
    generate_report_per_viewport(data)
