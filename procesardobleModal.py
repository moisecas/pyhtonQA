#procesar doble en paralelo con el modal confirmar cantidad de solicirtudes en el modal 

#!/usr/bin/env python3
# retiro_lote_unica_parallel.py — Procesa 1 iteración en paralelo (mcastro / mcastrodos),
# elige SIEMPRE "Procesar" (no desbloquear) y registra la cantidad en el modal de confirmación.

import re
import time
from multiprocessing import Process, Event, set_start_method
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

BASE_URL     = "https://backoffice-v2.qa.wcbackoffice.com/"
WITHDRAW_URL = BASE_URL + "admin/requests/withdrawal"

USERS = [
    {"name": "U1", "username": "mcastro",    "password": "N3wP@ssw0rd2024"},
    {"name": "U2", "username": "mcastrodos", "password": "N3wP@ssw0rd2024"},
]

HEADLESS = False  # True si no quieres ver ventanas

# ===== Selectores =====
X_LOGIN_USER   = "//input[@placeholder='Usuario']"
X_LOGIN_PASS   = "//input[@placeholder='Contraseña']"
X_LOGIN_SUBMIT = "//input[@value='Ingresar']"

# checkbox (tomamos la primera fila visible)
X_FIRST_CHECK  = "//tbody/tr[1]/td[1]//label/span"

# Botón "Ejecutar"
X_BTN_EJECUTAR = (
    "//button[@class='btn btn-secondary float-end me-1 btn-inverse']"
    " | //button[contains(@class,'btn-inverse') and contains(.,'Ejecutar')]"
)

# Select de acción (puede variar el name: action, 5973-action, <id>-action)
X_ACTION_SELECT = (
    "//select[@name='action']"
    " | //select[@name='5973-action']"
    " | //form//select[substring(@name, string-length(@name)-7)='-action']"
)

# Select de banco
X_BANK_SELECT = "//select[@name='bank']"

# Botón Guardar (preferencia y fallback)
X_BTN_GUARDAR_PREF = "//button[@class='btn btn-primary float-end']"
X_BTN_GUARDAR_FALL = "//button[@class='btn btn-secondary float-end me-1 btn-inverse']"

# Modal confirmación y botón "Sí"
X_MODAL_ANY = (
    "//div[contains(@class,'modal') and contains(@class,'show')]"
    " | //div[contains(@class,'swal2-container') and contains(@class,'swal2-show')]"
)
X_CONFIRM_SI = "//button[normalize-space()='Sí' and contains(@class,'btn-danger')]"


def js_click(driver, el):
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)


def wait_and_click(driver, wait, xpath):
    el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.15)
    js_click(driver, el)
    return el


def select_by_text_if_present(select_el, text) -> bool:
    """Intenta seleccionar por texto exacto; si no está, intenta 'contiene' (case-insensitive)."""
    sel = Select(select_el)
    try:
        sel.select_by_visible_text(text)
        return True
    except NoSuchElementException:
        for opt in sel.options:
            if text.lower() in opt.text.strip().lower():
                opt.click()
                return True
    return False


def choose_action_procesar(driver, wait) -> bool:
    """Abre acciones (Ejecutar) y deja 'Procesar' seleccionado. No intenta desbloquear."""
    wait_and_click(driver, wait, X_BTN_EJECUTAR)
    action_select = wait.until(EC.visibility_of_element_located((By.XPATH, X_ACTION_SELECT)))
    sel = Select(action_select)
    opts = [o.text.strip() for o in sel.options]
    print("Opciones de acción:", opts)
    ok = select_by_text_if_present(action_select, "Procesar")
    return ok


def read_selected_count_from_table(driver) -> int:
    """Cuenta checkboxes marcados en la tabla (fallback si el modal no lo indica)."""
    try:
        return len(driver.find_elements(By.XPATH, "//tbody//input[@type='checkbox' and @checked]"))
    except Exception:
        return 0


def read_count_from_modal_text(text: str) -> int | None:
    """
    Intenta extraer la cantidad desde el texto del modal.
    Busca patrones como: 'Procesar 3 solicitudes', '3 solicitud(es)', o en último caso el primer entero.
    """
    m = re.search(r"(\d+)\s+solicitud", text, flags=re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"solicitud(?:es)?\s*:\s*(\d+)", text, flags=re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{1,4})\b", text)  # número suelto como último recurso
    if m:
        return int(m.group(1))
    return None


def worker(user, ready_event, start_event, headless=False):
    name = user["name"]
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 20)

    try:
        # Login
        print(f"🔐 [{name}] Login…")
        driver.get(BASE_URL)
        wait.until(EC.visibility_of_element_located((By.XPATH, X_LOGIN_USER))).send_keys(user["username"])
        wait.until(EC.visibility_of_element_located((By.XPATH, X_LOGIN_PASS))).send_keys(user["password"])
        wait_and_click(driver, wait, X_LOGIN_SUBMIT)
        time.sleep(1.0)

        # Retiros
        print(f"➡️  [{name}] Ir a Retiros…")
        driver.get(WITHDRAW_URL)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//tbody")))
        except TimeoutException:
            pass

        # Sincroniza inicio con el otro proceso
        ready_event.set()
        start_event.wait()

        # ======= SOLO 1 ITERACIÓN EN PARALELO =======
        print(f"— [{name}] Iteración única —")

        # 1) Seleccionar checkbox 1ª fila
        try:
            checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, X_FIRST_CHECK)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
            time.sleep(0.2)
            js_click(driver, checkbox)
        except StaleElementReferenceException:
            checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, X_FIRST_CHECK)))
            js_click(driver, checkbox)

        # 2) Abrir "Ejecutar" y dejar "Procesar"
        if not choose_action_procesar(driver, wait):
            print(f"⚠️ [{name}] No hay opción 'Procesar'. Se omite.")
            try:
                js_click(driver, checkbox)  # desmarcar
            except Exception:
                pass
            return

        # 3) Espera solicitada
        time.sleep(5)

        # 4) Banco = BCI
        bank_select = wait.until(EC.visibility_of_element_located((By.XPATH, X_BANK_SELECT)))
        Select(bank_select).select_by_visible_text("BCI")

        # 5) Guardar
        try:
            btn_guardar = wait.until(EC.element_to_be_clickable((By.XPATH, X_BTN_GUARDAR_PREF)))
        except TimeoutException:
            btn_guardar = wait.until(EC.element_to_be_clickable((By.XPATH, X_BTN_GUARDAR_FALL)))
        js_click(driver, btn_guardar)

        # 6) Leer modal de confirmación: cantidad de solicitudes
        solicitudes_modal = None
        try:
            modal = WebDriverWait(driver, 6).until(EC.visibility_of_element_located((By.XPATH, X_MODAL_ANY)))
            modal_text = modal.text.strip()
            solicitudes_modal = read_count_from_modal_text(modal_text)
            print(f"   [{name}] Modal: {modal_text}")
            if solicitudes_modal is not None:
                print(f"   [{name}] Cantidad detectada en modal: {solicitudes_modal}")
            else:
                print(f"   [{name}] No se detectó cantidad explícita en modal.")
        except TimeoutException:
            print(f"   [{name}] No apareció modal visible (timeout).")

        # Fallback: contar seleccionados en tabla
        if solicitudes_modal is None:
            seleccionadas = read_selected_count_from_table(driver)
            print(f"   [{name}] Seleccionadas en tabla (fallback): {seleccionadas}")

        # 7) Confirmar “Sí” (si aparece)
        for i in range(3):
            try:
                yes_btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, X_CONFIRM_SI)))
                js_click(driver, yes_btn)
                print(f"   [{name}] Confirmación {i+1}")
                time.sleep(0.4)
            except TimeoutException:
                break

        time.sleep(0.8)
        print(f"✅ [{name}] Flujo único completado.")

    except Exception as e:
        print(f"❌ [{name}] Error:", e)
    finally:
        driver.quit()


if __name__ == "__main__":
    # Windows: arranque seguro del multiprocessing
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    ready1, ready2 = Event(), Event()
    start_together = Event()

    p1 = Process(target=worker, args=(USERS[0], ready1, start_together, HEADLESS))
    p2 = Process(target=worker, args=(USERS[1], ready2, start_together, HEADLESS))

    p1.start(); p2.start()
    # Esperar a que ambos estén en la pantalla de Retiros
    ready1.wait(); ready2.wait()
    # Disparar ejecución simultánea
    start_together.set()

    p1.join(); p2.join()
    print("🏁 Paralelo finalizado.")
