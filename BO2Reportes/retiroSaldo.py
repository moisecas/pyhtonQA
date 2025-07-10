#!/usr/bin/env python3
import os
import asyncio
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
    {
        "name": "QA",
        "base_url": "https://backoffice-v2.qa.wcbackoffice.com",
        "username": "efermin",
        "password": os.getenv("EFERMIN_PASS")
    },
    {
        "name": "QA2",
        "base_url": "https://backoffice-v2.qa.wcbackoffice.com",
        "username": "ddiaz",
        "password": os.getenv("DDIAZ_PASS")
    },
]

PLAYER_LIST_PATH    = "/reports/player-list"
USERNAME_FILTER     = "//input[@id='table-filter-user-name-filter']"
FILTER_BUTTON       = "//button[normalize-space()='Filtrar']"
MINUS_ICON_XPATH    = (
    "//td[contains(@class,'d-none d-sm-table-cell text-center')]"
    "//a[contains(@title,'Restar balance al jugador MOISECAS')][normalize-space()='-']"
)

async def adjust_player_withdrawal(page):
    # 1) Filtrar jugador
    await page.fill(USERNAME_FILTER, "MOISECAS")
    await page.click(FILTER_BUTTON)
    await page.wait_for_selector(MINUS_ICON_XPATH, timeout=10_000)

    # 2) Abrir modal de retiro
    await page.click(MINUS_ICON_XPATH, force=True)

    # 3) Esperar a que el modal esté visible
    modal_selector = "div#withdrawalBalanceModal.show"
    await page.wait_for_selector(modal_selector, state="visible", timeout=10_000)

    # 4) Esperar al input de monto visible y habilitado
    amount_input = page.locator("input#amount-withdrawalBalanceModal")
    await amount_input.wait_for(state="visible", timeout=10_000)
    if not await amount_input.is_enabled():
        raise RuntimeError("El campo de monto está deshabilitado")

    # 5) Rellenar monto de retiro
    await amount_input.fill("1.100,00", force=True)

    # 6) Click en "Guardar" dentro del modal
    save_btn = page.locator(f"{modal_selector} >> span:has-text('Guardar')")
    await save_btn.wait_for(state="visible", timeout=5_000)
    await save_btn.click(force=True)

    # 7) Esperar a que el modal se cierre
    await page.wait_for_selector(modal_selector, state="detached", timeout=10_000)
    await page.wait_for_timeout(500)

async def run_user(browser, cfg):
    ctx = await browser.new_context(
        accept_downloads=True,
        record_video_dir=str(VIDEO_DIR / cfg["name"]),
        record_video_size={"width": 1280, "height": 720}
    )
    page = await ctx.new_page()

    print(f"\n🔑 {cfg['name']}: Logueando…")
    await page.goto(cfg["base_url"], wait_until="networkidle")
    await page.fill("input[placeholder='Usuario']", cfg["username"])
    await page.fill("input[placeholder='Contraseña']", cfg["password"])
    await page.click("input[value='Ingresar']")
    await page.wait_for_load_state("networkidle")

    print(f"➡️ {cfg['name']}: Navegando a /reports/player-list")
    await page.goto(cfg["base_url"] + PLAYER_LIST_PATH, wait_until="networkidle")
    crumb = (await page.text_content("li.breadcrumb-item.active") or "").strip()
    print(f"   • Breadcrumb: «{crumb}»")

    print(f"   • {cfg['name']}: Realizando retiro…")
    await adjust_player_withdrawal(page)

    await ctx.close()
    vids = list((VIDEO_DIR / cfg["name"]).glob("*.webm"))
    for v in vids:
        print(f"  📹 Vídeo guardado: {v}")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        await asyncio.gather(*(run_user(browser, cfg) for cfg in USERS))
        await browser.close()
    print(f"\n🏁 Completado. Revisa los vídeos en: {VIDEO_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
