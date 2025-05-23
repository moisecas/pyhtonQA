from playwright.sync_api import sync_playwright
from datetime import datetime
import html as hm

def extract_background_styles(url):
    """
    Navega a la URL y extrae de cada elemento
    todas las propiedades CSS que comienzan con 'background'.
    Devuelve lista de dicts con tag, snippet y styles (map).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        data = page.evaluate("""
            () => {
                const out = [];
                const props = [
                  'background', 'backgroundImage', 'backgroundColor',
                  'backgroundSize', 'backgroundPosition',
                  'backgroundRepeat', 'backgroundAttachment',
                  'backgroundOrigin', 'backgroundClip'
                ];
                document.querySelectorAll('*').forEach(el => {
                    const cs = window.getComputedStyle(el);
                    const styles = {};
                    props.forEach(pn => {
                        const v = cs.getPropertyValue(pn);
                        if (v && v !== 'none' && !v.startsWith('rgba(0, 0, 0, 0)')) {
                            styles[pn] = v;
                        }
                    });
                    if (Object.keys(styles).length === 0) return;

                    // Construir snippet de forma segura
                    let snippet = el.tagName.toLowerCase();
                    if (el.id) {
                        snippet += `#${el.id}`;
                    } else if (el.classList && el.classList.length > 0) {
                        snippet += `.${el.classList[0]}`;
                    }
                    snippet += '…';

                    out.push({ tag: el.tagName.toLowerCase(), snippet, styles });
                });
                return out;
            }
        """)
        browser.close()
        return data

def generate_bg_styles_report(url, items, filename="background_styles_report.html"):
    """
    Genera un HTML listando cada elemento y sus propiedades de background.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = ""
    for it in items:
        tag     = hm.escape(it["tag"])
        snippet = hm.escape(it["snippet"])
        style_lines = ""
        for pn, v in it["styles"].items():
            style_lines += f"<div><strong>{pn}</strong>: <code>{hm.escape(v)}</code></div>"
        rows += (
            "<tr>"
            f"<td><code>{tag}</code></td>"
            f"<td>{snippet}</td>"
            f"<td>{style_lines}</td>"
            "</tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte de Estilos de Fondo</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; }}
    th {{ background: #f4f4f4; }}
    code {{ background: #eee; padding: 2px 4px; display: inline-block; }}
    div {{ margin: 2px 0; }}
  </style>
</head>
<body>
  <h1>Reporte de Estilos CSS de Fondo</h1>
  <p><strong>URL evaluada:</strong> {url}</p>
  <p><strong>Fecha generación:</strong> {now}</p>
  <table>
    <thead>
      <tr>
        <th>Etiqueta</th>
        <th>Snippet</th>
        <th>Propiedades de Fondo</th>
      </tr>
    </thead>
    <tbody>
{rows}    </tbody>
  </table>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Informe generado: {filename}")

if __name__ == "__main__":
    URL = "https://skin2-latamwin.qa.andes-system.com/"
    items = extract_background_styles(URL)
    generate_bg_styles_report(URL, items)
