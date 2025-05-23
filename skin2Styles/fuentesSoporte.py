#evaluar soporte del jugador page 


#login skin2 y evalua las fuentes de deposito

from playwright.sync_api import sync_playwright
from datetime import datetime
import html as hm

# Credenciales y URLs
USER = "TEST_GM2"
PASSWORD = "Cc12345678@@"
LOGIN_URL = "https://skin2-latamwin.qa.andes-system.com/"
TARGET_URL = "https://skin2-latamwin.qa.andes-system.com/support/contact"

def extract_elements_with_fonts_after_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # 1) Login
        page.goto(LOGIN_URL)
        page.click("button:has-text('Ingresar')")
        page.fill("input[placeholder='Usuario']", USER)
        page.fill("input[placeholder='Contraseña']", PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        # 2) Cerrar posible modal
        try:
            page.click("xpath=//header[@class='flex items-baseline justify-between gap-5 py-5']//*[name()='svg']", timeout=3000)
        except:
            pass
        # 3) Ir a Withdrawals
        page.goto(TARGET_URL)
        page.wait_for_load_state("networkidle")
        # 4) Recoger cada elemento con texto y su fontFamily
        data = page.evaluate("""
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
        browser.close()
        return data

def generate_detailed_withdrawals_report(items, filename="support_contact_detailed_report.html"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte Detallado de Fuentes en support_contact</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; vertical-align: top; }}
    th {{ background: #f4f4f4; }}
    td.content {{ max-width: 300px; word-wrap: break-word; }}
    code {{ background: #eee; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>Reporte Detallado de Fuentes en support_contact</h1>
  <p><strong>URL:</strong> {TARGET_URL}</p>
  <p><strong>Generado:</strong> {now}</p>
  <table>
    <thead>
      <tr><th>Etiqueta</th><th>Contenido</th><th>Font Family</th></tr>
    </thead>
    <tbody>
"""
    for it in items:
        tag     = hm.escape(it["tag"])
        content = hm.escape(it["content"])
        font    = hm.escape(it["font"])
        html += (
            f"      <tr>\n"
            f"        <td><code>{tag}</code></td>\n"
            f"        <td class='content'>{content}</td>\n"
            f"        <td><code>{font}</code></td>\n"
            f"      </tr>\n"
        )
    html += """    </tbody>
  </table>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Informe generado: {filename}")

if __name__ == "__main__":
    elements = extract_elements_with_fonts_after_login()
    generate_detailed_withdrawals_report(elements)
