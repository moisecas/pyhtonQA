#doble consulta a balance-skin 

import os
import asyncio
import shutil
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ————— Carga del .env —————
project_root = Path(__file__).parent
load_dotenv(project_root.parent / ".env")

# ————— Directorio de vídeos —————
VIDEO_DIR = project_root / "videos"
VIDEO_DIR.mkdir(exist_ok=True)

# ————— Usuarios y credenciales —————
USERS = [
    {"name": "QA",  "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "efermin", "password": os.getenv("EFERMIN_PASS")},
    {"name": "QA2", "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "ddiaz",  "password": os.getenv("DDIAZ_PASS")},
]

# ————— Rutas y selectores —————
BALANCE_SKIN_PATH = "/reports/balance-skin"
FILTER_BUTTON     = "//button[normalize-space()='Filtrar']"
EXPORT_BUTTON     = "//a[@class='btn waves-effect waves-light btn-primary']"
LOGIN_USER        = "input[placeholder='Usuario']"
LOGIN_PASS        = "input[placeholder='Contraseña']"
LOGIN_BTN         = "input[value='Ingresar']"

async def export_balance_skin(page, base_url: str):
    # Navega directamente a balance-skin
    await page.goto(base_url + BALANCE_SKIN_PATH, wait_until="networkidle")
    print("   • Navegado a Balance Skin")

    # Pulsar "Filtrar"
    await page.click(FILTER_BUTTON)
    await page.wait_for_selector(EXPORT_BUTTON)
    print("   • Filtro aplicado")

    # Disparar descarga y esperar
    async with page.expect_download() as dl_info:
        await page.click(EXPORT_BUTTON)
    download = await dl_info.value
    src_path = await download.path()
    filename = download.suggested_filename or src_path.name

    # Mover a carpeta de Descargas del usuario
    downloads_dir = Path.home() / "Downloads"
    downloads_dir.mkdir(exist_ok=True)
    dest_path = downloads_dir / filename
    shutil.move(src_path, dest_path)
    print(f"   • Archivo movido a Descargas: {dest_path}")

    # Esperar 5s antes de cerrar
    await page.wait_for_timeout(5000)

async def run_user(browser, cfg):
    ctx = await browser.new_context(
        accept_downloads=True,
        record_video_dir=str(VIDEO_DIR / cfg["name"]),
        record_video_size={"width": 1280, "height": 720}
    )
    page = await ctx.new_page()

    # Login
    print(f"\n🔑 {cfg['name']}: Logueando…")
    await page.goto(cfg["base_url"], wait_until="networkidle")
    await page.fill(LOGIN_USER, cfg["username"])
    await page.fill(LOGIN_PASS, cfg["password"])
    await page.click(LOGIN_BTN)
    await page.wait_for_load_state("networkidle")

    # Export balance-skin
    print(f"➡️ {cfg['name']}: Exportando balance-skin…")
    try:
        await export_balance_skin(page, cfg["base_url"])
    except PlaywrightTimeout:
        print(f"   ⚠️ {cfg['name']}: Timeout al exportar balance-skin")

    # Cerrar context (graba vídeo)
    await ctx.close()

    # Listar vídeo generado
    vids = list((VIDEO_DIR / cfg["name"]).glob("*.webm"))
    for v in vids:
        print(f"  📹 {cfg['name']}: Vídeo -> {v}")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        # Ejecutar ambos usuarios en paralelo
        await asyncio.gather(*(run_user(browser, cfg) for cfg in USERS))
        await browser.close()
    print(f"\n🏁 Completado. Vídeos en: {VIDEO_DIR} y archivos en ~/Downloads")

if __name__ == "__main__":
    asyncio.run(main())
