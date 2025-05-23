
#!/usr/bin/env python3
# tournaments_responsive_validation.py

import os
import html
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuración ---
URL = "https://skin2-latamwin.qa.andes-system.com/"

# Viewports a testar
VIEWPORTS = [
    ("desktop",   1360, 768),
    ("mobile-sm",  375, 667),
    ("mobile-md",  414, 896),
]

# Selectores clave por sección
ELEMENTS = {
    "sección_torneos":  "div[data-testid='swiper-section-middle-custom-id']",
    "titulo_torneos":   "div[data-testid='swiper-section-middle-custom-id'] >> text=Torneos",
    "btn_anterior":     "button[data-testid='swiper-navigation-custom-prev-button-id']",
    "btn_siguiente":    "button[data-testid='swiper-navigation-custom-next-button-id']",
    "carta_activa":     "div.slick-slide.slick-current div[data-testid^='tournament-card-']",
    "btn_unirme":       "button[data-testid='tournament-join-button-test-id']",
}

# Valores esperados por viewport
EXPECTED = {
    "desktop":   {"full_width": 1360, "cards_visible": 2},
    "mobile-sm": {"full_width": 375,  "cards_visible": 1},
    "mobile-md": {"full_width": 414,  "cards_visible": 1},
}

REPORT_DIR = "reports/tournaments"
os.makedirs(REPORT_DIR, exist_ok=True)


def px(val: str) -> int:
    """Convierte '123px' a entero 123 o devuelve 0 si falla."""
    try:
        return int(val.replace("px", "").strip())
    except:
        return 0


def main():
    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp_name, vp_w, vp_h in VIEWPORTS:
            page = browser.new_page()
            page.set_viewport_size({"width": vp_w, "height": vp_h})
            page.goto(URL, wait_until="networkidle")

            # 1) Validación estática de elementos
            for key, sel in ELEMENTS.items():
                locator = page.locator(sel).first
                try:
                    locator.wait_for(state="visible", timeout=5000)
                except:
                    rows.append({
                        "vp": vp_name,
                        "elem": key,
                        "status": "❌",
                        "detail": "no visible",
                        "img": ""
                    })
                    continue

                box = locator.bounding_box() or {}
                w, h = int(box.get("width", 0)), int(box.get("height", 0))

                styles = locator.evaluate(
                    """el => {
                        const cs = getComputedStyle(el);
                        return {
                          padL: parseInt(cs.paddingLeft),
                          padR: parseInt(cs.paddingRight),
                          gap: parseInt(cs.gap||0),
                          fontSize: cs.fontSize,
                          disabled: el.disabled===true
                        }
                    }"""
                )

                errors = []

                # ancho full-width de sección
                if key == "sección_torneos":
                    total = w + styles["padL"] + styles["padR"]
                    esperado = EXPECTED[vp_name]["full_width"]
                    if abs(total - esperado) > 2:
                        errors.append(f"ancho {total}px≠{esperado}px")

                # estado de botones al cargar
                if key == "btn_anterior" and not styles["disabled"]:
                    errors.append("prev debería iniciarse disabled")
                if key == "btn_siguiente" and styles["disabled"]:
                    errors.append("next debería iniciarse enabled")

                # título: tamaño de fuente mínimo
                if key == "titulo_torneos":
                    fs = px(styles["fontSize"])
                    if fs < 20:
                        errors.append(f"font-size muy pequeño ({fs}px)")

                # capturar screenshot
                img = f"{vp_name}_{key}.png"
                path = os.path.join(REPORT_DIR, img)
                locator.screenshot(path=path)

                rows.append({
                    "vp": vp_name,
                    "elem": key,
                    "status": "✅" if not errors else "❌",
                    "detail": "; ".join(errors),
                    "img": img
                })

            # 2) Validación responsive de cards visibles
            wrapper = page.locator(ELEMENTS["sección_torneos"] + " .slick-track").first
            card0   = page.locator(ELEMENTS["carta_activa"]).first

            w_wrap = int((wrapper.bounding_box() or {}).get("width", 0))
            w_card = int((card0.bounding_box() or {}).get("width",  0))
            fit = w_card and round(w_wrap / w_card)

            exp_cards = EXPECTED[vp_name]["cards_visible"]
            status = "✅" if fit == exp_cards else "❌"
            detail = "" if fit == exp_cards else f"{fit} visibles ≠ {exp_cards}"

            rows.append({
                "vp": vp_name,
                "elem": "cards_visibles",
                "status": status,
                "detail": detail,
                "img": ""
            })

            page.close()

        browser.close()

    # --- Generar informe HTML ---
    html_rows = ""
    for r in rows:
        # Construye la celda de imagen sin anidar f-strings
        img_cell = f'<img src="{r["img"]}" style="max-width:200px">' if r["img"] else ""
        html_rows += f"""
      <tr>
        <td>{html.escape(r['vp'])}</td>
        <td>{html.escape(r['elem'])}</td>
        <td style="text-align:center">{r['status']}</td>
        <td>{html.escape(r['detail'])}</td>
        <td>{img_cell}</td>
      </tr>"""

    report_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Validación Responsive “Torneos”</title>
  <style>
    body {{ font-family:sans-serif; padding:20px }}
    table {{ border-collapse:collapse; width:100% }}
    th, td {{ border:1px solid #ccc; padding:8px }}
    th {{ background:#f4f4f4 }}
  </style>
</head>
<body>
  <h1>Validación Responsive – Sección “Torneos”</h1>
  <p><strong>URL:</strong> {URL}</p>
  <p><strong>Fecha:</strong> {timestamp}</p>
  <table>
    <thead>
      <tr><th>Viewport</th><th>Elemento</th><th>Status</th><th>Detalle</th><th>Captura</th></tr>
    </thead>
    <tbody>
{html_rows}
    </tbody>
  </table>
</body>
</html>"""

    report_path = os.path.join(REPORT_DIR, "responsive_validation_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    print(f"✅ Reporte generado: {report_path}")


if __name__ == "__main__":
    main()
