#!/usr/bin/env python3
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ————— Carga del .env —————
project_root = Path(__file__).parent
load_dotenv(project_root.parent / ".env")

# ————— Directorio de vídeos y debug —————
VIDEO_DIR = project_root / "videos"
VIDEO_DIR.mkdir(exist_ok=True)
DEBUG_DIR = project_root / "debug"
DEBUG_DIR.mkdir(exist_ok=True)

USERS = [
    {"name": "QA",  "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "efermin", "password": os.getenv("EFERMIN_PASS")},
    {"name": "QA2", "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "ddiaz",   "password": os.getenv("DDIAZ_PASS")},
]

TARGET_USERNAME = "nuevo_usuario_50"

PLAYER_LIST_PATH      = "/reports/player-list"
USERNAME_FILTER_INPUT = "input#table-filter-user-name-filter"
TABLE_ROW_SELECTOR    = "table tbody tr"

async def adjust_player_balance(page, username, ctx_name):
    # 1) Esperar a que todo cargue
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    # 2) Escribir el username en el campo filtro
    await page.wait_for_selector(USERNAME_FILTER_INPUT, timeout=10000)
    await page.fill(USERNAME_FILTER_INPUT, "")
    await page.click(USERNAME_FILTER_INPUT)
    await page.type(USERNAME_FILTER_INPUT, username, delay=150)
    await asyncio.sleep(500)

    # 3) Localizar el botón “Filtrar” por texto y clic
    filter_btn = page.locator("button", has_text="Filtrar")
    await filter_btn.scroll_into_view_if_needed()
    await filter_btn.click()
    # Dar tiempo al backend/frontend para recargar
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1500)

    # 4) Screenshot para verificar
    shot = DEBUG_DIR / f"{ctx_name}_after_filter.png"
    await page.screenshot(path=shot)
    print(f"[DEBUG] Captura tras filtrar en: {shot}")

    # 5) Buscar la fila con nuestro username
    row = page.locator(
        TABLE_ROW_SELECTOR,
        has=page.locator(f"td:has-text('{username}')")
    )
    await row.wait_for(state="visible", timeout=20000)

    # 6) Dentro de esa fila, hacer clic en “+”
    plus_btn = row.locator("a.btn.btn-primary", has_text="+")
    await plus_btn.wait_for(state="visible", timeout=10000)
    await plus_btn.scroll_into_view_if_needed()
    await plus_btn.click(force=True)

    # 7) Modal de recarga
    modal = "div#addBalanceModal.show"
    await page.wait_for_selector(modal, state="visible", timeout=15000)

    # 8) Rellenar monto y guardar
    amt = page.locator("input#amount-addBalanceModal")
    await amt.wait_for(state="visible", timeout=10000)
    await amt.fill("1.000,00", force=True)
    save_btn = page.locator(f"{modal} button[type='submit']")
    await save_btn.click(force=True)

    # 9) Esperar cierre del modal
    await page.wait_for_selector(modal, state="detached", timeout=15000)

async def run_user(browser, cfg):
    ctx = await browser.new_context(
        record_video_dir=str(VIDEO_DIR / cfg["name"]),
        record_video_size={"width":1280,"height":720}
    )
    page = await ctx.new_page()

    print(f"\n🔑 {cfg['name']}: Logueando…")
    await page.goto(cfg["base_url"], wait_until="networkidle")
    await asyncio.sleep(1)
    await page.fill("input[placeholder='Usuario']", cfg["username"])
    await page.fill("input[placeholder='Contraseña']", cfg["password"])
    await page.click("input[value='Ingresar']")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    print(f"➡️ {cfg['name']}: Navegando a {PLAYER_LIST_PATH}")
    await page.goto(cfg["base_url"] + PLAYER_LIST_PATH, wait_until="networkidle")
    await asyncio.sleep(1)
    print(f"   • Breadcrumb: «{(await page.text_content('li.breadcrumb-item.active') or '').strip()}»")

    print(f"   • {cfg['name']}: Ajustando balance de {TARGET_USERNAME}…")
    try:
        await adjust_player_balance(page, TARGET_USERNAME, cfg["name"])
        print(f"✅ {cfg['name']}: Balance ajustado correctamente.")
    except PlaywrightTimeoutError:
        print(f"❌ {cfg['name']}: Timeout al filtrar o encontrar la fila “{TARGET_USERNAME}”. Revisa debug/")
    except Exception as e:
        print(f"❌ {cfg['name']}: Error ajustando balance:", e)

    await ctx.close()
    for v in (VIDEO_DIR / cfg["name"]).glob("*.webm"):
        print(f"  📹 Vídeo: {v}")

async def main():
    async with async_playwright() as pw:
        # slow_mo para visualizar cada paso
        browser = await pw.chromium.launch(headless=True, slow_mo=100)
        await asyncio.gather(*(run_user(browser, u) for u in USERS))
        await browser.close()
    print("\n🏁 Completado. Revisa videos en:", VIDEO_DIR, "y debug en:", DEBUG_DIR)

if __name__ == "__main__":
    asyncio.run(main())
