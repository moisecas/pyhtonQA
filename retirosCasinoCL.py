
# genera retiros en casinoenchile dev 

#!/usr/bin/env python3
# withdrawals_casinoenchile.py — genera retiros en casinoenchile.dev.wcbackoffice.com

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://casinoenchile.dev.wcbackoffice.com/"
WITHDRAW_URL = "https://casinoenchile.dev.wcbackoffice.com/balance/withdrawal"

# ===== Lista de jugadores (ajusta según tus pruebas) =====
players = [
  "moisecasdos"
]

# ===== Credenciales =====
fixed_password = "DelUnoAl24++"

# ===== Selectores =====
LOGIN_OPEN_BTN_XP = "//a[@class='theme-btn loginModalBtn']"
ACCOUNT_LABEL_XP  = "//label[@for='2298']"          # <— ajusta si cambia el for/id
AMOUNT_INPUT_XP   = "//input[@id='withdrawal']"
WITHDRAW_BTN_XP   = "//button[@id='btn-save']"

# Botón de cierre de modal (lo nuevo que pediste)
CLOSE_MODAL_BTN_XP = "//button[@type='button' and contains(@class,'close') and @data-dismiss='modal']"

# Fallbacks para inputs de login en el modal
USERNAME_XPS = [
    "//input[@name='username']",
    "//input[@id='username']",
    "//input[contains(@placeholder,'Usuario')]",
    "//input[contains(@placeholder,'Correo') or contains(@placeholder,'Email')]",
    "//input[@type='text' or @type='email']"
]
PASSWORD_XPS = [
    "//input[@name='password']",
    "//input[@id='password']",
    "//input[contains(@placeholder,'Contraseña')]",
    "//input[contains(@placeholder,'Password')]",
    "//input[@type='password']"
]
SUBMIT_LOGIN_XPS = [
    "//button[@type='submit']",
    "//button[normalize-space()='Ingresar']",
    "//button[contains(.,'Entrar') or contains(.,'Login') or contains(.,'Ingresar')]",
]

# ===== Utilidades =====
def find_click(driver, wait, xpaths, timeout=10_000):
    """Click en el primer xpath disponible (con JS fallback)."""
    for xp in (xpaths if isinstance(xpaths, (list, tuple)) else [xpaths]):
        try:
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            try:
                el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", el)
            return True
        except TimeoutException:
            continue
    return False

def find_fill(driver, wait, xpaths, text, clear=True, timeout=10_000):
    """Fill en el primer xpath visible."""
    for xp in (xpaths if isinstance(xpaths, (list, tuple)) else [xpaths]):
        try:
            el = wait.until(EC.visibility_of_element_located((By.XPATH, xp)))
            if clear:
                try: el.clear()
                except Exception: pass
            el.send_keys(text)
            return True
        except TimeoutException:
            continue
    return False

def click_if_present(driver, xpath, short_timeout_ms=2500):
    """Intentar clickear si aparece (no falla si no aparece)."""
    try:
        WebDriverWait(driver, short_timeout_ms//1000).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        ).click()
        time.sleep(0.2)
        print("[INFO] Modal de promo/notificación cerrado.")
        return True
    except Exception:
        # intento JS sobre el primero visible
        try:
            for el in driver.find_elements(By.XPATH, xpath):
                if el.is_displayed() and el.is_enabled():
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.2)
                    print("[INFO] Modal cerrado vía JS.")
                    return True
        except Exception:
            pass
        return False

def wait_any_visible(driver, xpaths, timeout=10_000):
    end = time.time() + (timeout/1000)
    last_err = None
    for xp in xpaths:
        while time.time() < end:
            try:
                el = driver.find_element(By.XPATH, xp)
                if el.is_displayed():
                    return el
            except Exception as e:
                last_err = e
            time.sleep(0.2)
    if last_err: raise last_err
    raise TimeoutException("Ningún xpath visible")

def do_withdraw_for_user(username: str):
    print(f"Procesando retiro para: {username}")
    opts = Options()
    # opts.add_argument("--headless=new")  # descomenta para headless
    driver = webdriver.Chrome(options=opts)
    wait   = WebDriverWait(driver, 12)

    try:
        # 1) Home
        driver.get(BASE_URL)
        driver.maximize_window()
        time.sleep(0.6)  # deja que aparezcan modales si hay

        # 1.1) Cerrar modal si aparece (lo nuevo)
        click_if_present(driver, CLOSE_MODAL_BTN_XP, short_timeout_ms=2500)

        # 2) Abrir modal de login
        if not find_click(driver, wait, LOGIN_OPEN_BTN_XP):
            raise TimeoutException("No se pudo abrir el modal de login")

        time.sleep(0.3)

        # 3) Rellenar usuario y password
        if not find_fill(driver, wait, USERNAME_XPS, username):
            raise TimeoutException("No se encontró input de usuario en el modal")
        if not find_fill(driver, wait, PASSWORD_XPS, fixed_password):
            raise TimeoutException("No se encontró input de contraseña en el modal")

        # 4) Submit login
        if not find_click(driver, wait, SUBMIT_LOGIN_XPS):
            pw = wait_any_visible(driver, PASSWORD_XPS)
            try: pw.submit()
            except Exception: driver.execute_script("arguments[0].form?.submit?.()", pw)

        time.sleep(1.2)  # espera breve a que autentique

        # 5) Ir directo a la página de Retiros
        driver.get(WITHDRAW_URL)

        # 6) Seleccionar la cuenta (label for='2298')
        if not find_click(driver, wait, ACCOUNT_LABEL_XP):
            raise TimeoutException("No se encontró la cuenta a seleccionar (label for='2298'). Ajusta ACCOUNT_LABEL_XP.")

        # 7) Escribir monto 1000
        if not find_fill(driver, wait, AMOUNT_INPUT_XP, "1000"):
            raise TimeoutException("No se encontró el input de monto (#withdrawal).")

        # 8) Click en Retirar
        if not find_click(driver, wait, WITHDRAW_BTN_XP):
            raise TimeoutException("No se pudo hacer clic en el botón Retirar (#btn-save).")

        # 9) Confirmación
        try:
            WebDriverWait(driver, 10).until(EC.any_of(
                EC.visibility_of_element_located((By.XPATH, "//*[contains(@class,'alert-success') or contains(@class,'toast-success')]")),
                EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Retiro') and contains(text(),'exitos')]")),
                EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'solicit') and contains(text(),'retiro')]"))
            ))
            print(f"✅ [{username}] Retiro solicitado correctamente.")
        except TimeoutException:
            print(f"⚠️ [{username}] No se confirmó visualmente el retiro. Revisa manualmente.")

    except Exception as e:
        print(f"❌ [{username}] Error durante el flujo de retiro:", e)

    finally:
        time.sleep(1.5)
        driver.quit()

# ===== Runner secuencial =====
if __name__ == "__main__":
    for player in players:
        do_withdraw_for_user(player)
        time.sleep(0.8)
