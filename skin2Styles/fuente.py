#evalua funtes de skin2 secciones q no requiren login

from playwright.sync_api import sync_playwright
from datetime import datetime
import html as hm

def extract_elements_with_fonts(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        data = page.evaluate("""
            () => {
                const elems = Array.from(document.querySelectorAll('*'));
                const results = [];
                elems.forEach(el => {
                    // 1) Tomar texto o placeholder
                    let text = el.textContent.trim();
                    if (!text && el.placeholder) text = el.placeholder;
                    // 2) Si está vacío, lo descartamos
                    if (!text) return;
                    // 3) Limitar a 100 caracteres
                    if (text.length > 100) text = text.slice(0, 100) + '…';
                    // 4) Leer la fuente computada
                    const font = window.getComputedStyle(el).fontFamily;
                    results.push({ tag: el.tagName.toLowerCase(), content: text, font });
                });
                return results;
            }
        """)
        browser.close()
        return data

def generate_detailed_report(url, items, filename="detailed_font_report.html"):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # f‑string con dobles llaves para CSS válido
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte Detallado de Tipos de Letra</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; }}
    th {{ background: #f4f4f4; }}
    td.content {{ max-width: 400px; word-wrap: break-word; }}
    code {{ background: #eee; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>Reporte Detallado de Tipos de Letra</h1>
  <p><strong>URL evaluada:</strong> {url}</p>
  <p><strong>Fecha:</strong> {date_str}</p>
  <table>
    <thead>
      <tr>
        <th>Etiqueta</th>
        <th>Contenido</th>
        <th>Font Family</th>
      </tr>
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
    print(f"✅ Informe detallado generado: {filename}")

if __name__ == "__main__":
    url   = "https://skin2-latamwin.qa.andes-system.com/about/terms_conditions"
    items = extract_elements_with_fonts(url)
    generate_detailed_report(url, items)
