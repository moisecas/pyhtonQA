#!/usr/bin/env python3
# playwright_register_flow.py

import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://skin2-latamwin.qa.andes-system.com"

# Datos de registro
RUT       = "20797514-1"
FIRST     = "Juan"
LAST      = "Pérez"
BIRTH_DAY = "miércoles, 27 de junio de 2007"
USERNAME  = "nuevo_usuario_01"
EMAIL     = "feimebeiyeida-9170@yopmail.com"
PHONE     = "56982886569"
PASSWORD  = "Cc12345678@@"
CITY      = "Santiago"
COUNTRY   = "Chile"

SELECTORS = {
    # Nuevo: botón "Regístrate" en home
    "register_button": "//div[@class='flex items-center justify-center gap-2 max-lg:hidden']//button[normalize-space()='Regístrate']",
    "rut":                "//input[@placeholder='RUT']",
    "first_name":         "//input[@placeholder='Nombre']",
    "last_name":          "//input[@placeholder='Apellido']",
    "birth_input":        "//input[@id='birth_date']",
    "birth_day":          f"//div[@aria-label='Choose {BIRTH_DAY}']",
    "birth_confirm":      "//div[contains(@class,'peer-checked')]//*[name()='svg']",
    "next_button":        "//button[@type='submit']",
    "username":           "//input[@placeholder='Nombre de usuario']",
    "email":              "//input[@placeholder='Correo']",
    "phone":              "//input[@placeholder='Celular']",
    "password":           "//input[@placeholder='Contraseña']",
    "confirm_password":   "//input[@placeholder='Confirmar contraseña']",
    "city":               "//input[@placeholder='Ciudad']",
    "country_select":     "//select[@name='country_id']",
    "terms_checkbox":     "//div[@data-testid='terms-and-conditions-link-id']//*[name()='svg']",
    "accept_button":      "//button[normalize-space()='Acepto']",
    "sms_checkbox":       "//div[@role='button']//*[name()='svg']//*[contains(@fill,'currentCol')]",
    "second_accept":      "(//button[normalize-space()='Acepto'])[2]",
    "modal_checkbox":     "//body//section[@role='document']//label[1]//*[name()='svg']",
    "final_button":       "//span[@class='me-2 uppercase']",
}

def register_flow(page):
    # 1) Ir a home y esperar el DOM
    page.goto(BASE_URL, wait_until="networkidle")
    # (Opcional) asegurar viewport de desktop para que no se oculte:
    page.set_viewport_size({"width": 1440, "height": 900})

    # 2) Localizar el botón y hacer click via JS
    page.wait_for_selector(SELECTORS["register_button"], state="attached", timeout=5000)
    page.evaluate("""
      () => {
        const btn = document.querySelector("button[data-testid='sign-up-button-test-id']");
        if (btn) btn.click();
      }
    """)
    time.sleep(1)

    # 2) RUT, nombre y apellido
    page.fill(SELECTORS["rut"], RUT)
    page.fill(SELECTORS["first_name"], FIRST)
    page.fill(SELECTORS["last_name"], LAST)

    # 3) Fecha de nacimiento
    page.click(SELECTORS["birth_input"])
    page.wait_for_selector(SELECTORS["birth_day"], timeout=5000)
    page.click(SELECTORS["birth_day"])
    page.click(SELECTORS["birth_confirm"])

    # 4) Siguiente
    page.click(SELECTORS["next_button"])
    time.sleep(1)

    # 5) Usuario / Email / Teléfono / Contraseñas / Ciudad
    page.fill(SELECTORS["username"], USERNAME)
    page.fill(SELECTORS["email"], EMAIL)
    page.fill(SELECTORS["phone"], PHONE)
    page.fill(SELECTORS["password"], PASSWORD)
    page.fill(SELECTORS["confirm_password"], PASSWORD)
    page.fill(SELECTORS["city"], CITY)

    # 6) País
    page.select_option(SELECTORS["country_select"], label=COUNTRY)
    time.sleep(0.5)

def register_flow(page):
  
    # 7) Términos y condiciones
    page.click("//div[@data-testid='terms-and-conditions-link-id']//div[@class='text-sm']")
    page.wait_for_timeout(5000)
    page.click("//button[normalize-space()='Acepto']")
    page.wait_for_timeout(500)

    # 8) Política de privacidad
    page.click("//div[@data-testid='privacy-policy-link-id']//div[@class='text-sm']")
    page.wait_for_timeout(5000)
    page.click("//button[normalize-space()='Acepto']")
    page.wait_for_timeout(500)

    # 9) Confirmar edad
    page.click("//span[contains(text(),'Confirmo que soy mayor de 18 años')]")
    page.wait_for_timeout(500)

    # 10) Botón final
    page.click(SELECTORS["final_button"])
    page.wait_for_timeout(1000)




   


    # 11) Confirmación
    try:
        page.wait_for_selector("text=¡Registro exitoso!", timeout=5000)
        print("✅ Registro completado correctamente.")
    except PlaywrightTimeoutError:
        print("⚠️ No se confirmó el registro, revisar manualmente.")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        try:
            register_flow(page)
        except Exception as e:
            print("❌ Error durante el flujo de registro:", e)
        finally:
            time.sleep(3)
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
