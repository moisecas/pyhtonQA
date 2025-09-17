#!/usr/bin/env python3
# bo2_parallel_tx_tab_fixed2.py — 2 sesiones en paralelo: Admin Skin(8) → pestaña "Transacción (Abono/Retiro)" → set 10000 y Guardar

import os
import re
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import expect

# ——— .env ———
project_root = Path(__file__).parent
load_dotenv(project_root.parent / ".env")

# ——— Paths ———
VIDEO_DIR = project_root / "videos"; VIDEO_DIR.mkdir(exist_ok=True)
DEBUG_DIR = project_root / "debug"; DEBUG_DIR.mkdir(exist_ok=True)

# ——— Credenciales / usuarios ———
USERS = [
    {"name": "QA",  "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "efermin", "password": os.getenv("EFERMIN_PASS")},
    {"name": "QA2", "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "ddiaz",   "password": os.getenv("DDIAZ_PASS")},
]

HEADLESS = os.getenv("HEADLESS", "false").strip().lower() in ("1","true","yes","on")

# ——— Destino admin (ajusta a dev/qa según entorno) ———
ADMIN_EDIT_URL = "https://backoffice-v2.qa.wcbackoffice.com/admin/skins/8/edit"
TX_TAB_TEXT_LITERAL = "Transacción (Abono/Retiro)"  # usar texto literal

# XPaths que tú pasaste (usaremos AMBOS como fallbacks)
TX_INPUT_USER_XP  = ("//body/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div[2]/form[1]/div[1]/div[2]/input[1]")
TX_INPUT_ALT_XP   = ("//body/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div[@role='tabpanel']/form[1]/div[1]/div[2]/input[1]")
TX_SUBMIT_USER_XP = ("//body/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div[@role='tabpanel']/form[@method='POST']/div/div[3]/input[1]")

# ——— Utilidades debug ———
async def screenshot(page, name):
    p = DEBUG_DIR / name
    await page.screenshot(path=p, full_page=True)
    print(f"[DEBUG] Screenshot: {p}")

# ——— Helpers de pestaña/panel ———
async def find_tx_tab(page):
    cands = [
        page.get_by_role("link", name=TX_TAB_TEXT_LITERAL),
        page.get_by_role("tab",  name=TX_TAB_TEXT_LITERAL),
        page.locator("a.nav-link", has_text=TX_TAB_TEXT_LITERAL),
        page.locator("a", has_text=TX_TAB_TEXT_LITERAL),
        page.locator("a,button,[role='tab']").filter(
            has_text=re.compile(r"Transacci[oó]n", re.I)
        ).filter(
            has_text=re.compile(r"Abono/?Retiro", re.I)
        ),
    ]
    for loc in cands:
        if await loc.count():
            return loc.first
    return None

async def get_panel_from_tab(page, tab_loc):
    # href / data-bs-target / aria-controls
    sel = None
    for attr in ("href", "data-bs-target", "aria-controls"):
        try:
            val = await tab_loc.get_attribute(attr)
            if val and val.startswith("#"):
                sel = val
                break
        except Exception:
            pass
    if sel:
        panel = page.locator(sel)
        if await panel.count():
            return panel.first
    # Fallback: el panel/tab-pane activo
    return page.locator(".tab-pane.active, [role='tabpanel'].active").first

# ——— Flujo dentro del admin ———
async def open_tx_tab_and_set_amount(page, ctx_name, amount_str="10000"):
    # 1) Ir al edit del skin
    await page.goto(ADMIN_EDIT_URL, wait_until="networkidle")
    await asyncio.sleep(0.5)

    # 2) Abrir la pestaña
    tab = await find_tx_tab(page)
    if not tab:
        await screenshot(page, f"{ctx_name}_no_tab.png")
        raise RuntimeError("No se encontró la pestaña 'Transacción (Abono/Retiro)'")

    await tab.scroll_into_view_if_needed()
    await tab.click()
    # deja que renderice el contenido del tab
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.3)

    panel = await get_panel_from_tab(page, tab)
    await expect(panel).to_be_visible()

    # 3) Input de monto: prueba varias estrategias y registra cuál funcionó
    input_cands = [
        page.locator(f"xpath={TX_INPUT_USER_XP}"),
        page.locator(f"xpath={TX_INPUT_ALT_XP}"),
        panel.locator("form input[type='number']").first,
        panel.locator("form input[placeholder*='monto' i]").first,
        panel.locator("form input[name*='amount' i], form input[name*='saldo' i], form input[name*='abono' i]").first,
        # último recurso: cualquier input visible no hidden/submit/checkbox/radio dentro del form del panel
        panel.locator("form input:not([type='hidden']):not([type='submit']):not([type='checkbox']):not([type='radio'])").first,
    ]

    the_input = None
    used = ""
    for idx, loc in enumerate(input_cands):
        try:
            if await loc.count():
                # Asegúrate de que esté visible o scrolleable
                try:
                    await loc.scroll_into_view_if_needed()
                except Exception:
                    pass
                await expect(loc).to_be_visible()
                the_input = loc
                used = f"cand#{idx+1}"
                break
        except Exception:
            continue

    if not the_input:
        await screenshot(page, f"{ctx_name}_no_input.png")
        raise RuntimeError("No se encontró el input de monto en el tab de Transacción.")

    print(f"[DEBUG] [{ctx_name}] input elegido: {used}")
    await the_input.fill("")
    await the_input.type(amount_str, delay=25)

    # 4) Botón Guardar dentro del panel
    btn_cands = [
        panel.locator("form button[type='submit']").first,
        panel.locator("form input[type='submit']").first,
        page.locator(f"xpath={TX_SUBMIT_USER_XP}"),
    ]
    the_btn = None
    usedb = ""
    for idx, loc in enumerate(btn_cands):
        try:
            if await loc.count():
                try:
                    await loc.scroll_into_view_if_needed()
                except Exception:
                    pass
                await expect(loc).to_be_enabled()
                the_btn = loc
                usedb = f"cand#{idx+1}"
                break
        except Exception:
            continue

    if not the_btn:
        await screenshot(page, f"{ctx_name}_no_submit.png")
        raise RuntimeError("No se encontró el botón Guardar en el tab de Transacción.")

    print(f"[DEBUG] [{ctx_name}] submit elegido: {usedb}")
    await the_btn.click()

    # 5) Espera breve y screenshot final
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.5)
    await screenshot(page, f"{ctx_name}_after_save.png")
    print(f"✅ [{ctx_name}] Monto '{amount_str}' enviado en pestaña Transacción.")

# ——— Runner por usuario ———
async def run_user(browser, cfg):
    ctx = await browser.new_context(
        record_video_dir=str(VIDEO_DIR / cfg["name"]),
        record_video_size={"width":1280,"height":720},
        viewport={"width":1280, "height":720},
        locale="es-ES"
    )
    await ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

    page = await ctx.new_page()
    page.set_default_timeout(18000)

    try:
        print(f"\n🔑 {cfg['name']}: Logueando…")
        await page.goto(cfg["base_url"], wait_until="networkidle")
        await asyncio.sleep(0.6)
        await page.fill("input[placeholder='Usuario']", cfg["username"])
        await page.fill("input[placeholder='Contraseña']", cfg["password"])
        await page.click("input[value='Ingresar']")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.6)

        print(f"➡️ {cfg['name']}: Ir a Admin Skin 8 (qa) y abrir pestaña Transacción…")
        await open_tx_tab_and_set_amount(page, cfg["name"], amount_str="10000")

        print(f"✅ {cfg['name']}: Finalizado.")
    except PlaywrightTimeoutError as e:
        print(f"❌ {cfg['name']}: Timeout en algún paso. {e}")
        await screenshot(page, f"{cfg['name']}_timeout.png")
    except Exception as e:
        print(f"❌ {cfg['name']}: Error: {e}")
        await screenshot(page, f"{cfg['name']}_error.png")
    finally:
        await ctx.tracing.stop(path=str(DEBUG_DIR / f"{cfg['name']}_trace.zip"))
        await ctx.close()
        for v in (VIDEO_DIR / cfg["name"]).glob("*.webm"):
            print(f"  📹 Vídeo: {v}")
        tz = DEBUG_DIR / f"{cfg['name']}_trace.zip"
        if tz.exists():
            print(f"  🧵 Trace: {tz}")

# ——— Main (PARALELO) ———
async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS, slow_mo=80)
        await asyncio.gather(*(run_user(browser, u) for u in USERS))  # paralelo real
        await browser.close()
    print("\n🏁 Completado. Revisa videos en:", VIDEO_DIR, "y debug en:", DEBUG_DIR)

if __name__ == "__main__":
    asyncio.run(main())
