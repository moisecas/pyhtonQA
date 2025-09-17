
# crear jugadores skin2 

import time
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://skin2-latamwin.dev.andes-system.com/"

# ————— Datos de registro —————
RUT       = "12209454-5"
FIRST     = "Juan"
LAST      = "Pérez"
BIRTH_DAY = "lunes, 10 de septiembre de 2007"
USERNAME  = "nuevo_usuario_75"
EMAIL     = "xuhuvogeffi-6541@yopmail.com"
PHONE     = "977446117"
PASSWORD  = "Cc12345678@@"
CITY      = "Santiago"
COUNTRY   = "Chile"

SELECTORS = {
    "register_button": (
        "//div[@class='flex items-center justify-center gap-2 max-lg:hidden']"
        "//button[normalize-space()='Regístrate']"
    ),
    "rut":              "//input[@placeholder='RUT']",
    "first_name":       "//input[@placeholder='Nombre']",
    "last_name":        "//input[@placeholder='Apellido']",
    "birth_input":      "//input[@id='birth_date']",
    "birth_day":        f"//div[@aria-label='Choose {BIRTH_DAY}']",
    "next1":            "//button[@data-testid='button-submit-step-1']",
    "username":         "//input[@placeholder='Nombre de usuario']",
    "email":            "//input[@placeholder='Correo electrónico']",
    "phone":            "//input[@placeholder='Nro. de Teléfono']",
    "password":         "//input[@placeholder='Contraseña']",
    "confirm_password": "//input[@placeholder='Confirmar contraseña']",
    "city":             "//input[@placeholder='Ciudad']",
    "country_select":   "//select[@name='country_id']",
    "next2":            "//button[@data-testid='button-submit-step-2']",
    "accept_button":    "//button[normalize-space()='Estoy de acuerdo']",
    "final_button":     "//span[@class='mr-1']",
}

TERMS_LINK_SELECTORS = [
    "//span[normalize-space()='términos y condiciones']"
]
PRIVACY_LINK_SELECTORS = [
    "//span[normalize-space()='políticas de privacidad']"
]
CONFIRM_AGE_SELECTOR = "//span[contains(text(),'Confirmo que soy mayor de 18 años')]"

def pick_and_click(page, xpaths, timeout=5_000):
    for xp in xpaths:
        try:
            page.wait_for_selector(xp, timeout=timeout)
            page.click(xp)
            return True
        except:
            continue
    return False

def register_flow(page):
    page.goto(BASE_URL, wait_until="networkidle")
    page.set_viewport_size({"width": 1440, "height": 900})

    # 1) Click "Regístrate"
    page.wait_for_selector(SELECTORS["register_button"], timeout=10_000)
    page.click(SELECTORS["register_button"])
    time.sleep(1)

    # 2) Paso 1: RUT, nombre, apellido
    page.fill(SELECTORS["rut"], RUT)
    page.fill(SELECTORS["first_name"], FIRST)
    page.fill(SELECTORS["last_name"], LAST)

    # 3) Fecha de nacimiento
    page.click(SELECTORS["birth_input"])
    page.wait_for_selector(SELECTORS["birth_day"], timeout=10_000)
    page.click(SELECTORS["birth_day"])
    time.sleep(0.5)
    if not page.input_value(SELECTORS["birth_input"]):
        raise RuntimeError("La fecha no se llenó correctamente")

    # 4) Siguiente paso 1
    page.wait_for_selector("button[data-testid='button-submit-step-1']:not([disabled])", timeout=10_000)
    page.click(SELECTORS["next1"])
    time.sleep(1)

    # 5) Paso 2: resto de campos
    page.fill(SELECTORS["username"], USERNAME)
    page.fill(SELECTORS["email"], EMAIL)
    page.fill(SELECTORS["phone"], PHONE)
    page.fill(SELECTORS["password"], PASSWORD)
    page.fill(SELECTORS["confirm_password"], PASSWORD)
    page.fill(SELECTORS["city"], CITY)
    page.select_option(SELECTORS["country_select"], label=COUNTRY)

    # 6) Aceptar Términos y Condiciones
    if pick_and_click(page, TERMS_LINK_SELECTORS):
        page.wait_for_selector(SELECTORS["accept_button"], timeout=10_000)
        page.click(SELECTORS["accept_button"])
        time.sleep(0.5)

    # 7) Aceptar Políticas de Privacidad
    if pick_and_click(page, PRIVACY_LINK_SELECTORS):
        page.wait_for_selector(SELECTORS["accept_button"], timeout=10_000)
        page.click(SELECTORS["accept_button"])
        time.sleep(0.5)

    # 8) Confirmar edad
    page.wait_for_selector(CONFIRM_AGE_SELECTOR, timeout=10_000)
    page.click(CONFIRM_AGE_SELECTOR)
    time.sleep(0.5)

    # 9) Siguiente paso 2
    page.wait_for_selector("button[data-testid='button-submit-step-2']:not([disabled])", timeout=10_000)
    page.click(SELECTORS["next2"])
    time.sleep(1)

    # 10) Botón "Registrarme"
    page.wait_for_selector(SELECTORS["final_button"], timeout=10_000)
    page.click(SELECTORS["final_button"])
    time.sleep(1)

    # 11) Verificación final
    try:
        page.wait_for_selector("text=¡Registro exitoso!", timeout=5_000)
        print("✅ Registro completado correctamente.")
    except PlaywrightTimeoutError:
        print("⚠️ No se confirmó el registro, revisa manualmente.")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100, args=["--start-maximized"])
        ctx     = browser.new_context()
        page    = ctx.new_page()
        try:
            register_flow(page)
        except Exception as e:
            print("❌ Error durante el flujo de registro:", e)
        finally:
            time.sleep(3)
            ctx.close()
            browser.close()

if __name__ == "__main__":
    main()
