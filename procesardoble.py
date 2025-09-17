#retiro doble modulo retiros 

import time
from multiprocessing import Process, Event, set_start_method
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

BASE_URL = "https://backoffice-v2.qa.wcbackoffice.com/"
WITHDRAW_URL = "https://backoffice-v2.qa.wcbackoffice.com/admin/requests/withdrawal"

USERS = [
    {"name": "U1", "username": "mcastro",    "password": "N3wP@ssw0rd2024"},
    {"name": "U2", "username": "mcastrodos", "password": "N3wP@ssw0rd2024"},
]

HEADLESS = False  # true para que corra por debajo per mejor false para ver

# ===== Selectores =====
X_LOGIN_USER   = "//input[@placeholder='Usuario']"
X_LOGIN_PASS   = "//input[@placeholder='Contraseña']"
X_LOGIN_SUBMIT = "//input[@value='Ingresar']"

# Check de la primera solicitud 
X_FIRST_CHECK  = "//tbody/tr[1]/td[1]//label/span"

# NUEVOS selectores 
X_ACTION_SEL   = "//select[@name='5973-action']"                 # <- escoger 'Procesar'
X_BANK_SEL     = "//select[@name='bank']"                        # <- escoger 'BCI'
X_SAVE_BTN     = "//button[@class='btn btn-primary float-end']"  # exacto
X_SAVE_BTN_FBK = "//button[contains(@class,'btn-primary') and contains(@class,'float-end')]"  # fallback

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

def select_by_text(driver, wait, select_xpath, visible_text):
    sel_el = wait.until(EC.visibility_of_element_located((By.XPATH, select_xpath)))
    Select(sel_el).select_by_visible_text(visible_text)
    return sel_el

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
        time.sleep(1.2)

        # Ir a Retiros
        print(f"➡️  [{name}] Ir a Retiros…")
        driver.get(WITHDRAW_URL)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//tbody")))
        except TimeoutException:
            pass

        # sincronizar con otro proceso 
        ready_event.set()
        start_event.wait()

        # --- Flujo dos veces ---
        for run in range(2):
            print(f"— [{name}] Iteración {run+1} —")

            # (1) Seleccionar solicitud (primera fila)
            try:
                checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, X_FIRST_CHECK)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
                time.sleep(0.2)
                js_click(driver, checkbox)
            except StaleElementReferenceException:
                checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, X_FIRST_CHECK)))
                js_click(driver, checkbox)

            # (2) Seleccionar acción "Procesar"
            select_by_text(driver, wait, X_ACTION_SEL, "Procesar")

            # (3) Esperar 5 segundos (UI puede habilitar campos)
            time.sleep(5)

            # (4) Banco "BCI"
            select_by_text(driver, wait, X_BANK_SEL, "BCI")

            # (5) Guardar
            try:
                wait_and_click(driver, wait, X_SAVE_BTN)
            except TimeoutException:
                wait_and_click(driver, wait, X_SAVE_BTN_FBK)

          
            for i in range(3):
                try:
                    yes_btn = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Sí' and contains(@class,'btn-danger')]"))
                    )
                    js_click(driver, yes_btn)
                    print(f"   [{name}] Confirmación {i+1}")
                    time.sleep(0.4)
                except TimeoutException:
                    break

            time.sleep(1.2)

        print(f"✅ [{name}] Flujo completado.")
        time.sleep(1.5)

    except Exception as e:
        print(f"❌ [{name}] Error:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    ready1, ready2 = Event(), Event()
    start_together = Event()

    p1 = Process(target=worker, args=(USERS[0], ready1, start_together, HEADLESS))
    p2 = Process(target=worker, args=(USERS[1], ready2, start_together, HEADLESS))

    p1.start(); p2.start()
    # esperar a que ambos estén en la página de retiros
    ready1.wait(); ready2.wait()
    # disparar ejecución simultánea
    start_together.set()

    p1.join(); p2.join()
    print("🏁 Paralelo finalizado.")
