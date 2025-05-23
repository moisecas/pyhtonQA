# check_quick_access_report.py

from playwright.sync_api import sync_playwright, TimeoutError
from spellchecker import SpellChecker
import re, os, html
from datetime import datetime

# URL a probar
URL = "https://skin2-latamwin.qa.andes-system.com/"

# Viewports a validar
VIEWPORTS = [
    ("desktop",   1360, 768),
    ("mobile-sm",  375, 667),
    ("mobile-md",  414, 896),
]

# 1) Botones en la barra de accesos rápidos
QUICK_ACCESS_SELECTOR = "#onboarding-buttons-quick-access-bar-custom-id button"

# 2) Botones del Menú Cajero / Lobby
EXTRA_SELECTORS = {
    "Menú Cajero": "button:has-text('Cajero')",
    "Menú Lobby":  "button:has-text('Lobby')"
}

# Clases esperadas en cada botón
REQUIRED_CLASSES = {
    "font-serif","font-bold","py-2","px-2","rounded-lg","leading-[14.06px]",
    "text-sm","bg-primary-900","text-primary-100","pressed:bg-primary-500",
    "pressed:border","pressed:border-primary-900","disabled:bg-neutral-100",
    "disabled:text-neutral-200","disabled:pressed:bg-neutral-100",
    "disabled:pressed:border-none","!bg-button-quick-access",
    "pressed:!text-primary-700","!border-neutral-200","shadow-md",
    "transition-colors","flex","items-center","gap-0.5","!p-1","!pr-2",
    "!h-9","w-full","min-w-fit","md:!h-10","lg:w-auto","!text-xs",
    "!font-semibold","uppercase","!leading-5","md:!text-lg",
    "md:!leading-5","box","box-border"
}

# Inicializar corrector ortográfico en español
spell = SpellChecker(language="es")

def is_all_upper(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return all(c.isupper() for c in letters) if letters else True

def find_misspellings(text: str):
    words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+", text)
    bad = spell.unknown(w.lower() for w in words)
    return [w for w in words if w.lower() in bad]

def run_and_generate_report():
    results = []
    os.makedirs("reports", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, w, h in VIEWPORTS:
            page = browser.new_page()
            page.set_viewport_size({"width": w, "height": h})
            page.goto(URL, wait_until="networkidle")

            # –– Validar “Accesos Rápidos” ––
            try:
                page.wait_for_selector(QUICK_ACCESS_SELECTOR, timeout=5000)
            except TimeoutError:
                print(f"⚠️ [{name}] No se encontraron botones de accesos rápidos.")

            for handle in page.locator(QUICK_ACCESS_SELECTOR).element_handles():
                txt = (handle.text_content() or "").strip()
                if not txt:
                    continue

                # 1) Text-transform
                tt = handle.evaluate(
                    "el => getComputedStyle(el).getPropertyValue('text-transform')"
                )
                uc_ok = tt == "uppercase" or is_all_upper(txt)
                miss = find_misspellings(txt)
                spell_ok = not bool(miss)
                cls_attr = handle.get_attribute("class") or ""
                cls_set = set(cls_attr.split())
                classes_ok = REQUIRED_CLASSES.issubset(cls_set)

                results.append({
                    "section":      "Accesos Rápidos",
                    "resolution":   name,
                    "text":         txt,
                    "uppercase_ok": uc_ok,
                    "spell_ok":     spell_ok,
                    "misspellings": miss,
                    "classes_ok":   classes_ok,
                    "classes":      cls_attr
                })

            # –– Validar Menú Cajero / Lobby ––
            for section, sel in EXTRA_SELECTORS.items():
                try:
                    page.wait_for_selector(sel, timeout=3000)
                except TimeoutError:
                    print(f"⚠️ [{name}] No se encontró el botón “{section}”.")
                    continue

                for handle in page.locator(sel).element_handles():
                    txt = (handle.text_content() or "").strip()
                    if not txt:
                        continue

                    tt = handle.evaluate(
                        "el => getComputedStyle(el).getPropertyValue('text-transform')"
                    )
                    uc_ok = tt == "uppercase" or is_all_upper(txt)
                    miss = find_misspellings(txt)
                    spell_ok = not bool(miss)
                    cls_attr = handle.get_attribute("class") or ""
                    cls_set = set(cls_attr.split())
                    classes_ok = REQUIRED_CLASSES.issubset(cls_set)

                    results.append({
                        "section":      section,
                        "resolution":   name,
                        "text":         txt,
                        "uppercase_ok": uc_ok,
                        "spell_ok":     spell_ok,
                        "misspellings": miss,
                        "classes_ok":   classes_ok,
                        "classes":      cls_attr
                    })

            page.close()
        browser.close()

    # Construir filas de la tabla HTML
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = ""
    for r in results:
        uc = "✅" if r["uppercase_ok"] else "❌"
        sp = "✅" if r["spell_ok"]     else f"❌ {', '.join(r['misspellings'])}"
        cl = "✅" if r["classes_ok"]   else "❌"
        rows += f"""
      <tr>
        <td>{html.escape(r['resolution'])}</td>
        <td>{html.escape(r['section'])}</td>
        <td>{html.escape(r['text'])}</td>
        <td style="text-align:center">{uc}</td>
        <td style="text-align:center">{sp}</td>
        <td style="text-align:center">{cl}</td>
        <td><code>{html.escape(r['classes'])}</code></td>
      </tr>
    """

    if not rows:
        rows = """
      <tr>
        <td colspan="7" style="text-align:center">
          No se encontraron elementos para validar.
        </td>
      </tr>
    """

    # Generar HTML completo
    report_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte “Accesos Rápidos & Menú Cajero/Lobby”</title>
  <style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; vertical-align: top; }}
    th {{ background: #f4f4f4; }}
    code {{ display: block; white-space: pre-wrap; word-break: break-word; }}
  </style>
</head>
<body>
  <h1>Reporte “Accesos Rápidos” & “Menú Cajero / Lobby”</h1>
  <p><strong>URL evaluada:</strong> {URL}</p>
  <p><strong>Fecha generación:</strong> {now}</p>
  <table>
    <thead>
      <tr>
        <th>Resolución</th>
        <th>Sección</th>
        <th>Texto</th>
        <th>Mayúsculas</th>
        <th>Ortografía</th>
        <th>Clases OK</th>
        <th>Clase completa</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</body>
</html>
"""

    path = os.path.join("reports", "quick_access_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_html)

    print(f"✅ Reporte HTML generado: {path}")

if __name__ == "__main__":
    run_and_generate_report()
