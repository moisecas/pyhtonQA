#ir a conciliación de jugadores e iteracturar con dos usuarios sobre el reporte 

import os
from datetime import datetime
from playwright.sync_api import sync_playwright

# ————— Configuración —————
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

USERS = [
    {
        "name": "QA",
        "base_url": "https://backoffice-v2.qa.wcbackoffice.com",
        "username": "efermin",
        "password": "N3wP@ssw0rd2024",
    },
    {
        "name": "QA2",
        "base_url": "https://backoffice-v2.qa.wcbackoffice.com",
        "username": "ddiaz",
        "password": "N3wP@ssw0rd2024",
    }
]

CONCILIATION_PATH = "/reports/player-conciliation"
DATE_FILTER_ISO = "2024-01-01T00:00:00"  # ajustar si se necesita otro rango
FILTER_BUTTON      = "//button[normalize-space()='Filtrar']"
EXPORT_BUTTON_XPATH = "//a[contains(@class,'btn') and contains(@class,'btn-primary')]"

def login(page, base_url, user, pwd):
    page.goto(base_url, wait_until="networkidle")
    page.fill("input[placeholder='Usuario']", user)
    page.fill("input[placeholder='Contraseña']", pwd)
    page.click("input[value='Ingresar']")
    page.wait_for_load_state("networkidle")

def apply_date_filter(page, iso_date): #establece el filtro de fecha 
    page.evaluate(f"""
      () => {{
        const inp = document.querySelector('input.datetime-flatpickr');
        inp.removeAttribute('readonly');
        inp._flatpickr.setDate('{iso_date}');
      }}
    """)
    page.click(FILTER_BUTTON) # esperar a que la tabla se recargue 
    page.wait_for_selector("table tbody tr")

def export_report(page, user_label, iteration):#espera y captura descarga
    with page.expect_download() as dl_info:
        page.click(EXPORT_BUTTON_XPATH)
    download = dl_info.value
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_label}_conciliation_{iteration}_{timestamp}{os.path.splitext(download.suggested_filename)[1]}"
    path = os.path.join(DOWNLOAD_DIR, filename)
    download.save_as(path)
    print(f"✅ {user_label}: descarga #{iteration} guardada en {path}")

def run_for_user(browser, user_cfg):
    ctx = browser.new_context(
        accept_downloads=True,
        record_video_dir="videos",            # carpeta donde se guardan los videos
        record_video_size={"width": 1280, "height": 720}
    )
    page = ctx.new_page()


    print(f"\n🔑 Iniciando sesión en {user_cfg['name']} …")
    login(page, user_cfg["base_url"], user_cfg["username"], user_cfg["password"])

    url = user_cfg["base_url"] + CONCILIATION_PATH
    print(f"➡️ Navegando a {url}")
    page.goto(url, wait_until="networkidle")

    #confirmamos que estamos en la página correcta
    crumb = page.text_content("li.breadcrumb-item.active") or ""
    print(f"   • Breadcrumb: «{crumb.strip()}»")

    # aplicar filtro de fecha
    print("   • Aplicando filtro de fecha…")
    apply_date_filter(page, DATE_FILTER_ISO)

    # exportar dos veces
    print("   • Exportando reporte dos veces…")
    export_report(page, user_cfg["name"], 1)
    export_report(page, user_cfg["name"], 2)

    ctx.close() # cerrar contexto del navegador 

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for user_cfg in USERS:
            run_for_user(browser, user_cfg)

        browser.close()
    print("\n🏁 Todo completado. Los archivos están en:", DOWNLOAD_DIR) # ruta de descarga 

if __name__ == "__main__":
    main()
