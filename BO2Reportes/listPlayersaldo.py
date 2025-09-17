#ingresar con dos users a bo2 a cargar saldo 


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

USERS = [
    {"name": "QA",  "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "efermin", "password": os.getenv("EFERMIN_PASS")},
    {"name": "QA2", "base_url": "https://backoffice-v2.qa.wcbackoffice.com", "username": "ddiaz",   "password": os.getenv("DDIAZ_PASS")},
]

TARGET_USERNAME = "nuevo_usuario_50"

PLAYER_LIST_PATH       = "/reports/player-list"
USERNAME_FILTER_INPUT  = "input#table-filter-user-name-filter"
SKIN_SELECT_ID         = "table-filter-skin-filter"       # <select id="table-filter-skin-filter"> ... (wire:ignore + Select2)
TABLE_ROW_SELECTOR     = "table tbody tr"
FILTER_BUTTON_TEXT     = re.compile(r"^\s*Filtrar\s*$", re.I)
HEADLESS = os.getenv("HEADLESS", "false").strip().lower() in ("1","true","yes","on")
SKIN_NAME = os.getenv("SKIN_NAME", "").strip()  # etiqueta visible en el Select2 (p.ej. "GanaLucas", "CasinoEnChile")

LIVEWIRE_HINT = "/livewire/message"

# ——— Debug helpers ———
async def dump_table_html(page, ctx_name, tag):
    try:
        table = page.locator("table").first
        if await table.count():
            html = await table.evaluate("el => el.outerHTML")
            p = DEBUG_DIR / f"{ctx_name}_table_{tag}.html"
            p.write_text(html or "", encoding="utf-8")
            print(f"[DEBUG] Tabla guardada: {p}")
    except Exception as e:
        print("[DEBUG] No se pudo guardar tabla:", e)

async def dump_livewire_state(page, ctx_name, tag):
    try:
        data = await page.evaluate(r"""
            () => {
              try {
                const root = document.querySelector('[wire\\:id]');
                if (!root || !window.Livewire) return null;
                const id = root.getAttribute('wire:id');
                const c = window.Livewire.find(id);
                if (!c) return null;
                // Algunas versiones exponen serverMemo.data, otras snapshot.data
                const d = (c.serverMemo && c.serverMemo.data) || (c.snapshot && c.snapshot.data) || null;
                return d;
              } catch(e){ return {error: (''+e)}; }
            }
        """)
        p = DEBUG_DIR / f"{ctx_name}_livewire_{tag}.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[DEBUG] Livewire state guardado: {p}")
    except Exception as e:
        print("[DEBUG] No se pudo leer Livewire state:", e)

async def wait_rows_or_empty(page, timeout_ms=15000):
    empty_texts = ["No se encontraron elementos", "Sin resultados", "No results", "No data"]
    try:
        await page.wait_for_function(
            """([rowSel, empties]) => {
                const rows = document.querySelectorAll(rowSel);
                if (rows && rows.length > 0) return true;
                const txt = document.body.innerText || '';
                return empties.some(t => txt.includes(t));
            }""",
            (TABLE_ROW_SELECTOR, empty_texts),
            timeout=timeout_ms
        )
    except Exception:
        pass
    return await page.locator(TABLE_ROW_SELECTOR).count()

async def filters_panel_open(page):
    return await page.locator(USERNAME_FILTER_INPUT).is_visible()

async def open_filters_if_needed(page):
    if not await filters_panel_open(page):
        toggle = page.get_by_role("button", name=re.compile(r"^Filtros\b", re.I))
        if await toggle.count():
            await toggle.first.click()
            await page.wait_for_selector(USERNAME_FILTER_INPUT, state="visible", timeout=5000)

async def find_filter_button(page):
    cands = [
        page.locator(f"form:has({USERNAME_FILTER_INPUT})").get_by_role("button", name=FILTER_BUTTON_TEXT),
        page.get_by_role("button", name=FILTER_BUTTON_TEXT),
        page.locator("button:has-text('Filtrar')"),
        page.locator("input[type='submit'][value='Filtrar']"),
        page.locator(".btn:has-text('Filtrar')"),
    ]
    for loc in cands:
        if await loc.count():
            return loc.first
    return page.locator("button.__no_existe__")

# ——— Select2 helpers ———
def _select2_container_xpath(select_id: str) -> str:
    # <select id="..."> <span class="select2 select2-container">...</span>
    return f"//select[@id='{select_id}']/following-sibling::span[contains(@class,'select2')]"

async def select2_search_and_choose(page, select_id: str, visible_text: str):
    container = page.locator(f"xpath={_select2_container_xpath(select_id)}").first
    await expect(container).to_be_visible()
    await container.click()                           # abre el dropdown
    search = page.locator("input.select2-search__field").first
    await expect(search).to_be_visible()
    await search.fill(visible_text)
    # espera a que aparezca la opción en el dropdown y selecciona con Enter
    await page.wait_for_selector("li.select2-results__option", timeout=5000)
    # opcional: forzar match por texto, si aparece
    candidate = page.locator("li.select2-results__option", has_text=re.compile(re.escape(visible_text), re.I)).first
    if await candidate.count():
        await candidate.click()
    else:
        await page.keyboard.press("Enter")
    # espera a que se cierre el dropdown
    await page.wait_for_selector("input.select2-search__field", state="detached", timeout=5000)

async def get_select_options_text(page, select_id: str):
    try:
        return await page.evaluate(f"""
          () => Array.from(document.querySelectorAll('#{select_id} option'))
            .map(o => o.textContent.trim())
            .filter(t => !!t && t.toLowerCase() !== 'todos' and t.toLowerCase() !== 'seleccione')
        """)
    except Exception:
        return []

# ——— Click + esperar Livewire ———
async def click_and_wait_livewire(page, filter_btn, timeout=12000):
    # Espera la llamada /livewire/message y luego el render
    async with page.expect_response(lambda r: LIVEWIRE_HINT in r.url, timeout=timeout):
        await expect(filter_btn).to_be_visible()
        await expect(filter_btn).to_be_enabled()
        await filter_btn.scroll_into_view_if_needed()
        await filter_btn.click()
    # después del response, espera que desaparezca cualquier [wire:loading]
    loading = page.locator("[wire\\:loading]")
    if await loading.count():
        try:
            await loading.first.wait_for(state="hidden", timeout=timeout)
        except Exception:
            pass
    await page.wait_for_timeout(200)

# ——— Flujo principal ———
async def adjust_player_balance(page, username, ctx_name):
    await page.wait_for_load_state("networkidle")
    await open_filters_if_needed(page)

    # (opcional) identifica usuario del topbar
    try:
        top = (await page.locator("header,nav").inner_text()).strip()
        print(f"[DEBUG] Topbar: {top[:120]}")
    except Exception:
        pass

    # 0) Dump estado inicial
    await dump_livewire_state(page, ctx_name, "before")
    await dump_table_html(page, ctx_name, "before")

    # 1) Seleccionar SKIN si existe Select2
    select2_xpath = _select2_container_xpath(SKIN_SELECT_ID)
    has_skin_select2 = await page.locator(f"xpath={select2_xpath}").count() > 0

    tried_skins = []
    if has_skin_select2:
        # intentamos primero con SKIN_NAME si viene en .env
        if SKIN_NAME:
            print(f"[DEBUG] Seteando Skin via Select2: {SKIN_NAME}")
            await select2_search_and_choose(page, SKIN_SELECT_ID, SKIN_NAME)
            tried_skins.append(SKIN_NAME)
        else:
            # todavía no elegimos; lo haremos si no hay filas tras primer intento
            pass

    # 2) Escribir usuario
    await page.wait_for_selector(USERNAME_FILTER_INPUT, timeout=10000)
    inp = page.locator(USERNAME_FILTER_INPUT)
    await inp.fill("")
    await inp.fill(username)

    # 3) Click en Filtrar y esperar Livewire
    filter_btn = await find_filter_button(page)
    await click_and_wait_livewire(page, filter_btn)

    # 4) Verifica filas
    rows = await wait_rows_or_empty(page, timeout_ms=12000)
    print(f"[DEBUG] Filas tras primer Filtrar: {rows}")

    # 5) Si 0 filas y tenemos Select2 de Skin, rota skins visibles y reintenta
    if rows == 0 and has_skin_select2:
        options = await get_select_options_text(page, SKIN_SELECT_ID)  # etiquetas visibles
        # agrega opciones no probadas
        for label in options:
            if label and label not in tried_skins:
                print(f"[DEBUG] Reintentando con Skin: {label}")
                await select2_search_and_choose(page, SKIN_SELECT_ID, label)
                await click_and_wait_livewire(page, filter_btn)
                rows = await wait_rows_or_empty(page, timeout_ms=12000)
                print(f"[DEBUG] Filas con Skin={label}: {rows}")
                tried_skins.append(label)
                if rows > 0:
                    break

    # 6) Dumps finales
    await dump_livewire_state(page, ctx_name, "after")
    await dump_table_html(page, ctx_name, "after")
    shot = DEBUG_DIR / f"{ctx_name}_after_filter.png"
    await page.screenshot(path=shot)
    print(f"[DEBUG] Captura tras filtrar: {shot}")
    print(f"[DEBUG] Skins probados: {tried_skins}")

    if rows == 0:
        raise PlaywrightTimeoutError(
            f"Sin filas para '{username}'. Es casi seguro que es el SKIN: "
            f"{', '.join(tried_skins) or 'ninguno'}. Fija SKIN_NAME en .env con la etiqueta exacta del Select2."
        )
        

    # 7) Continuar con '+'
    row = page.locator(TABLE_ROW_SELECTOR).filter(
        has=page.get_by_text(re.compile(rf"\b{re.escape(username)}\b", re.I))
    ).first
    await row.wait_for(state="visible", timeout=15000)

    plus_btn = row.locator("a.btn.btn-primary", has_text="+")
    await expect(plus_btn).to_be_visible()
    await plus_btn.scroll_into_view_if_needed()
    await plus_btn.click()

    modal = "div#addBalanceModal.show"
    await page.wait_for_selector(modal, state="visible", timeout=15000)

    amt = page.locator("input#amount-addBalanceModal")
    await expect(amt).to_be_visible()
    await amt.fill("1.000,00")
    save_btn = page.locator(f"{modal} button[type='submit']")
    await expect(save_btn).to_be_enabled()
    await save_btn.click()
    await page.wait_for_selector(modal, state="detached", timeout=15000)

# ——— Runner ———
async def run_user(browser, cfg):
    ctx = await browser.new_context(
        record_video_dir=str(VIDEO_DIR / cfg["name"]),
        record_video_size={"width":1280,"height":720},
        viewport={"width":1280, "height":720},
        locale="es-ES"
    )
    await ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

    page = await ctx.new_page()
    page.set_default_timeout(12000)
    page.on("console", lambda m: print(f"[console] {m.type}: {m.text}"))

    print(f"\n🔑 {cfg['name']}: Logueando…")
    await page.goto(cfg["base_url"], wait_until="networkidle")
    await asyncio.sleep(1)
    await page.fill("input[placeholder='Usuario']", cfg["username"])
    await page.fill("input[placeholder='Contraseña']", cfg["password"])
    await page.click("input[value='Ingresar']")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    print(f"➡️ {cfg['name']}: Navegando a {PLAYER_LIST_PATH}")
    await page.goto(cfg["base_url"] + PLAYER_LIST_PATH, wait_until="domcontentloaded")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)
    print(f"   • Breadcrumb: «{(await page.text_content('li.breadcrumb-item.active') or '').strip()}»")

    print(f"   • {cfg['name']}: Ajustando balance de {TARGET_USERNAME}…")
    try:
        await adjust_player_balance(page, TARGET_USERNAME, cfg["name"])
        print(f"✅ {cfg['name']}: Balance ajustado correctamente.")
    except PlaywrightTimeoutError as e:
        print(f"❌ {cfg['name']}: Timeout/Empty tras filtrar “{TARGET_USERNAME}”. {e}")
        print("   Revisa el video y pon en .env: SKIN_NAME=<Etiqueta EXACTA del Select2> (tal como la ves manualmente).")
    except Exception as e:
        print(f"❌ {cfg['name']}: Error ajustando balance:", e)

    await ctx.tracing.stop(path=str(DEBUG_DIR / f"{cfg['name']}_trace.zip"))
    await ctx.close()

    for v in (VIDEO_DIR / cfg["name"]).glob("*.webm"):
        print(f"  📹 Vídeo: {v}")
    tz = DEBUG_DIR / f"{cfg['name']}_trace.zip"
    if tz.exists():
        print(f"  🧵 Trace: {tz}")

# ——— Main ———
async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS, slow_mo=100)
        # Secuencial para no “pisar” el BE
        for u in USERS:
            await run_user(browser, u)
        await browser.close()
    print("\n🏁 Completado. Revisa videos en:", VIDEO_DIR, "y debug en:", DEBUG_DIR)

if __name__ == "__main__":
    asyncio.run(main())
