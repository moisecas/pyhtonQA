#retiro de saldo desde lista de jugadores doble en paralelo varios clics 


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

PLAYER_LIST_PATH = "/reports/player-list"
USERNAME_FILTER  = "//input[@id='table-filter-user-name-filter']"
FILTER_BUTTON    = "//button[normalize-space()='Filtrar']"
MINUS_ICON_XPATH = (
    "//td[@class='d-none d-sm-table-cell text-center']"
    "//a[@title='Restar balance al jugador MOISECAS'][normalize-space()='-']"
)

async def withdraw_player_balance(page):
    # 1) Filtrar jugador
    await page.fill(USERNAME_FILTER, "MOISECAS")
    await page.wait_for_timeout(500)
    await page.click(FILTER_BUTTON)
    await page.wait_for_selector(MINUS_ICON_XPATH)

    # 2) Abrir modal de retiro
    await page.click(MINUS_ICON_XPATH, force=True)

    # 3) Esperar a que el modal esté abierto
    await page.wait_for_selector("div.modal.show div.modal-body", timeout=10000)

    # 4) Rellenar monto con formato "1.000,00"
    await page.fill("input#amount-withdrawalBalanceModal", "1.000,00", force=True)

    # 5) Hacer clic en "Guardar" dentro del modal
    modal_container = page.locator("div.modal.show")
    await modal_container.locator("button[type='submit']").click(force=True)

    # 6) Esperar a que el modal se cierre
    await page.wait_for_selector("div.modal.show", state="detached", timeout=10000)
    await page.wait_for_timeout(2000)

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
    await page.fill("input[placeholder='Usuario']", cfg["username"])
    await page.fill("input[placeholder='Contraseña']", cfg["password"])
    await page.click("input[value='Ingresar']")
    await page.wait_for_load_state("networkidle")

    # Ir a la lista de jugadores
    print(f"➡️ {cfg['name']}: /reports/player-list")
    await page.goto(cfg["base_url"] + PLAYER_LIST_PATH, wait_until="networkidle")
    crumb = (await page.text_content("li.breadcrumb-item.active") or "").strip()
    print(f"   • Breadcrumb: «{crumb}»")

    # Retirar balance
    print(f"   • {cfg['name']}: Retirando saldo…")
    await withdraw_player_balance(page)

    # Cerrar contexto para finalizar vídeo
    await ctx.close()

    # Mostrar ruta del vídeo generado
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
