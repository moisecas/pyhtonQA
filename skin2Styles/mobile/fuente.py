from playwright.sync_api import sync_playwright
from datetime import datetime
import html as hm

# Lista de tamaños de pantalla mobile a evaluar
default_viewports = [
    {"label": "iPhone SE", "width": 375, "height": 667},
    {"label": "iPhone 12 Pro", "width": 390, "height": 844},
    {"label": "Pixel 2", "width": 411, "height": 731},
    {"label": "Galaxy S9", "width": 360, "height": 740}
]


def extract_for_viewports(url, viewports=default_viewports):
    """
    Carga la URL en cada tamaño de viewport y extrae los elementos con texto y su font-family.
    Devuelve un dict: label -> list de {tag, content, font}.
    """
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for vp in viewports:
            page = browser.new_page()
            page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            page.goto(url)
            # Extraer datos
            items = page.evaluate("""
                () => {
                    const out = [];
                    document.querySelectorAll('*').forEach(el => {
                        let text = el.textContent.trim();
                        if (!text && el.placeholder) text = el.placeholder;
                        if (!text) return;
                        if (text.length > 100) text = text.slice(0,100) + '…';
                        const font = window.getComputedStyle(el).fontFamily;
                        out.push({ tag: el.tagName.toLowerCase(), content: text, font });
                    });
                    return out;
                }
            """)
            results[vp["label"]] = {"viewport": vp, "items": items}
            page.close()
        browser.close()
    return results


def generate_mobile_report(url, data, filename="detailed_font_mobile_report.html"):
    """
    Genera un HTML donde para cada viewport presenta una tabla con etiqueta, contenido y font.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte Tipos de Letra - Mobile Viewports</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    h1, h2 {{ margin-top: 1em; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; }}
    th {{ background: #f4f4f4; }}
    td.content {{ max-width: 400px; word-wrap: break-word; }}
    code {{ background: #eee; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>Reporte Detallado de Tipos de Letra</h1>
  <p><strong>URL evaluada:</strong> {url}</p>
  <p><strong>Fecha:</strong> {now}</p>
"""
    
    # Para cada viewport
    for label, info in data.items():
        vp = info["viewport"]
        items = info["items"]
        html += f"""
  <h2>{label} ({vp['width']}×{vp['height']})</h2>
  <table>
    <thead>
      <tr><th>Etiqueta</th><th>Contenido</th><th>Font Family</th></tr>
    </thead>
    <tbody>
"""
        for it in items:
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
    print(f"✅ Informe mobile generado: {filename}")


if __name__ == "__main__":
    URL = "https://skin2-latamwin.qa.andes-system.com/about/terms_conditions" 
    data = extract_for_viewports(URL)
    generate_mobile_report(URL, data)
