#!/usr/bin/env python3
# createPlayers_race.py — intenta registrar el MISMO usuario en paralelo y sincronizado

import time
import re
from multiprocessing import Process, Event, set_start_method
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://skin2-latamwin.dev.andes-system.com/"

# —— DATA: MISMA para ambos procesos (ajusta a tu caso) ——
DATA = {
    "RUT":       "10238513-6",
    "FIRST":     "Juan",
    "LAST":      "Pérez",
    "BIRTH_DAY": "lunes, 27 de agosto de 2007",
    "USERNAME":  "nuevo_usuario_58",                 # <— MISMO
    "EMAIL":     "kefreirixipei-3530@yopmail.com", # <— MISMO (si tu BE exige email único)
    "PHONE":     "56961313144",
    "PASSWORD":  "Cc12345678@@",
    "CITY":      "Santiago",
    "COUNTRY":   "Chile",
}

SELECTORS = {
    "register_button": (
        "//div[@class='flex items-center justify-center gap-2 max-lg:hidden']"
        "//button[normalize-space()='Regístrate']"
    ),
    "rut":              "//input[@placeholder='RUT']",
    "first_name":       "//input[@placeholder='Nombre']",
    "last_name":        "//input[@placeholder='Apellido']",
    "birth_input":      "//input[@id='birth_date']",
    "birth_day_tpl":    "//div[@aria-label='Choose {BIRTH_DAY}']",
    "next1":            "//button[@data-testid='button-submit-step-1']",
    "username":         "//input[@placeholder='Nombre de usuario']",
    "email":            "//input[@placeholder='Correo']",
    "phone":            "//input[@placeholder='Celular']",
    "password":         "//input[@placeholder='Contraseña']",
    "confirm_password": "//input[@placeholder='Confirmar contraseña']",
    "city":             "//input[@placeholder='Ciudad']",
    "country_select":   "//select[@name='country_id']",
    "next2":            "//button[@data-testid='button-submit-step-2']",
    "accept_button":    "//button[normalize-space()='Acepto']",
    "final_button":     "//span[@class='mr-1']",
}

TERMS_LINKS = [
    "//div[@data-testid='terms-and-conditions-link-id']//div[@class='text-sm']",
    "//span[normalize-space()='Términos y condiciones']",
]
PRIVACY_LINKS = [
    "//div[@data-testid='privacy-policy-link-id']//div[@class='text-sm']",
    "//span[normalize-space()='Políticas de privacidad']",
]
CONFIRM_AGE = "//span[contains(text(),'Confirmo que soy mayor de 18 años')]"

def pick_and_click(page, xpaths, timeout=5_000):
    for xp in xpaths:
        try:
            page.wait_for_selector(xp, timeout=timeout)
            page.click(xp)
            return True
        except Exception:
            continue
    return False

def fill_until_ready(page, data):
    page.goto(BASE_URL, wait_until="networkidle")
    page.set_viewport_size({"width": 1440, "height": 900})

    # Paso 0: abrir registro
    page.wait_for_selector(SELECTORS["register_button"], timeout=10_000)
    page.click(SELECTORS["register_button"])
    page.wait_for_timeout(400)

    # Paso 1
    page.fill(SELECTORS["rut"], data["RUT"])
    page.fill(SELECTORS["first_name"], data["FIRST"])
    page.fill(SELECTORS["last_name"], data["LAST"])

    # Fecha
    page.click(SELECTORS["birth_input"])
    birth_xpath = SELECTORS["birth_day_tpl"].format(BIRTH_DAY=data["BIRTH_DAY"])
    page.wait_for_selector(birth_xpath, timeout=10_000)
    page.click(birth_xpath)
    page.wait_for_timeout(200)

    # Siguiente
    page.wait_for_selector("button[data-testid='button-submit-step-1']:not([disabled])", timeout=10_000)
    page.click(SELECTORS["next1"])
    page.wait_for_timeout(400)

    # Paso 2
    page.fill(SELECTORS["username"], data["USERNAME"])
    page.fill(SELECTORS["email"], data["EMAIL"])
    page.fill(SELECTORS["phone"], data["PHONE"])
    page.fill(SELECTORS["password"], data["PASSWORD"])
    page.fill(SELECTORS["confirm_password"], data["PASSWORD"])
    page.fill(SELECTORS["city"], data["CITY"])
    page.select_option(SELECTORS["country_select"], label=data["COUNTRY"])

    # Accept TyC y Privacidad
    if pick_and_click(page, TERMS_LINKS):
        page.wait_for_selector(SELECTORS["accept_button"], timeout=10_000)
        page.click(SELECTORS["accept_button"])
        page.wait_for_timeout(200)
    if pick_and_click(page, PRIVACY_LINKS):
        page.wait_for_selector(SELECTORS["accept_button"], timeout=10_000)
        page.click(SELECTORS["accept_button"])
        page.wait_for_timeout(200)

    # Mayor de 18
    page.wait_for_selector(CONFIRM_AGE, timeout=10_000)
    page.click(CONFIRM_AGE)
    page.wait_for_timeout(200)

    # Paso 2 listo: botón “Siguiente”
    page.wait_for_selector("button[data-testid='button-submit-step-2']:not([disabled])", timeout=10_000)
    page.click(SELECTORS["next2"])
    page.wait_for_timeout(300)

    # En este punto solo falta “Registrarme” (final_button)
    page.wait_for_selector(SELECTORS["final_button"], timeout=10_000)

def click_final_and_report(page, who):
    # clic “Registrarme”
    page.click(SELECTORS["final_button"])
    page.wait_for_timeout(600)

    # Resultado: éxito o ya-existe
    try:
        page.wait_for_selector("text=¡Registro exitoso!", timeout=4_000)
        print(f"✅ [{who}] Registro completado.")
        return
    except PlaywrightTimeoutError:
        pass

    # Busca mensajes de error comunes
    error_candidates = [
        "ya existe", "ya está en uso", "duplicado",
        "correo ya existe", "usuario ya existe",
    ]
    try:
        html = page.content().lower()
        if any(tok in html for tok in error_candidates):
            print(f"🛑 [{who}] Rechazado por duplicado (usuario/email).")
        else:
            print(f"⚠️ [{who}] Sin confirmación ni error claro; revisar manualmente.")
    except Exception:
        print(f"⚠️ [{who}] Sin confirmación; revisar manualmente.")

def worker(name, data, ready_evt, start_evt, headed=True, slow_mo=100):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed, slow_mo=slow_mo, args=["--start-maximized"])
        ctx     = browser.new_context()
        page    = ctx.new_page()
        try:
            fill_until_ready(page, data)
            # Señala que llegó al botón final
            ready_evt.set()
            # Espera la orden del padre para pulsar a la vez
            start_evt.wait()
            click_final_and_report(page, name)
        except Exception as e:
            print(f"❌ [{name}] Error:", e)
        finally:
            page.wait_for_timeout(1200)
            ctx.close(); browser.close()

if __name__ == "__main__":
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    headed = True  # pon False si no quieres ventana

    # Eventos para sincronizar el envío
    ready1, ready2 = Event(), Event()
    go = Event()

    p1 = Process(target=worker, args=("P1", DATA, ready1, go, headed))
    p2 = Process(target=worker, args=("P2", DATA, ready2, go, headed))

    p1.start(); p2.start()

    # Espera a que ambos estén en el botón final
    ready1.wait(); ready2.wait()
    # Libera el click simultáneo
    go.set()

    p1.join(); p2.join()
    print("🏁 Race test finalizado.")
