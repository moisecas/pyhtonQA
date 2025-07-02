#!/usr/bin/env python3
import os
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# ————— Carga del .env —————
project_root = Path(__file__).parent
load_dotenv(project_root.parent / ".env")

# ————— Directorio de vídeos —————
VIDEO_DIR = project_root / "videos"
VIDEO_DIR.mkdir(exist_ok=True)

USERS = [
    {"name":"QA",  "base_url":"https://backoffice-v2.qa.wcbackoffice.com",  "username":"efermin", "password":os.getenv("EFERMIN_PASS")},
    {"name":"QA2", "base_url":"https://backoffice-v2.qa.wcbackoffice.com",  "username":"ddiaz",  "password":os.getenv("DDIAZ_PASS")},
]

PLAYER_LIST_PATH = "/reports/player-list"
USERNAME_FILTER  = "//input[@id='table-filter-user-name-filter']"
FILTER_BUTTON    = "//button[normalize-space()='Filtrar']"
PLUS_ICON_XPATH  = (
    "//td[@class='d-none d-sm-table-cell text-center' "
    "and .//a[@title='Agregar balance al jugador MOISECAS']]"
    "//a[normalize-space()='+']"
)

async def adjust_player_balance(page):
    # 1) Filtrar
    await page.fill(USERNAME_FILTER, "MOISECAS")
    await page.wait_for_timeout(500)
    await page.click(FILTER_BUTTON)
    await page.wait_for_selector(PLUS_ICON_XPATH)

    # 2) Abrir modal
    await page.click(PLUS_ICON_XPATH, force=True)
    await page.wait_for_selector("div#addBalanceModal.show")

    # 3) Rellenar monto
    await page.fill("div#addBalanceModal.show input#amount", "1000", force=True)

    # 4) Cinco clics al botón “Guardar” vía JS
    await page.evaluate("""
      () => {
        const btn = document.querySelector('div#addBalanceModal.show button[type="submit"]');
        for (let i = 0; i < 5; i++) btn.click();
      }
    """)

    # 5) Cerrar modal
    await page.wait_for_selector("div#addBalanceModal.show", state="detached")
    await page.wait_for_timeout(2000)

async def run_user(browser, cfg):
    # cada user con su propio context → graba vídeo
    ctx = await browser.new_context(
        accept_downloads=True,
        record_video_dir=str(VIDEO_DIR / cfg["name"]),
        record_video_size={"width":1280,"height":720}
    )
    page = await ctx.new_page()

    print(f"\n🔑 {cfg['name']}: Logueando…")
    await page.goto(cfg["base_url"], wait_until="networkidle")
    await page.fill("input[placeholder='Usuario']", cfg["username"])
    await page.fill("input[placeholder='Contraseña']", cfg["password"])
    await page.click("input[value='Ingresar']")
    await page.wait_for_load_state("networkidle")

    print(f"➡️ {cfg['name']}: /reports/player-list")
    await page.goto(cfg["base_url"] + PLAYER_LIST_PATH, wait_until="networkidle")
    crumb = (await page.text_content("li.breadcrumb-item.active") or "").strip()
    print(f"   • Breadcrumb: «{crumb}»")

    print(f"   • {cfg['name']}: Ajustando balance…")
    await adjust_player_balance(page)

    # cerrar context → VIDEO se escribe aquí
    await ctx.close()

    # listar el fichero de vídeo generado
    vids = list((VIDEO_DIR / cfg["name"]).glob("*.webm"))
    for v in vids:
        print(f"  📹 Vídeo guardado: {v}")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        # lanzar ambos usuarios en paralelo
        await asyncio.gather(*(run_user(browser, cfg) for cfg in USERS))
        await browser.close()
    print(f"\n🏁 Completado. Revisa los vídeos en: {VIDEO_DIR}")

if __name__=="__main__":
    asyncio.run(main())
