#!/usr/bin/env python3
# retiros_parallel.py — Ejecuta el flujo de retiro 2 veces en paralelo para 2 usuarios

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

HEADLESS = False  # pon True si no quieres ver ventanas

# ————— Selectores —————
X_LOGIN_USER   = "//input[@placeholder='Usuario']"
X_LOGIN_PASS   = "//input[@placeholder='Contraseña']"
X_LOGIN_SUBMIT = "//input[@value='Ingresar']"

X_FIRST_CHECK  = "//tbody/tr[1]/td[1]/div/label/span"
X_EJECUTAR_BTN = "//button[contains(@class,'btn-inverse')]"
X_ACTION_SEL   = "//select[@name='action']"
X_BANK_SEL     = "//select[@name='bank']"
X_SAVE_BTN     = "//button[@type='submit' and contains(@class,'btn-primary')]"
X_CONFIRM_SI   = "//button[@class='btn btn-danger' and normalize-space()='Sí']"

def js_click(driver, el):
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)

def worker(user, ready_event, start_event, headless=False):
    name = user["name"]
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 20)

    def wait_and_click(xpath):
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.2)
        js_click(driver, el)
        return el

    try:
        print(f"🔐 [{name}] Login…")
        driver.get(BASE_URL)
        wait.until(EC.visibility_of_element_located((By.XPATH, X_LOGIN_USER))).send_keys(user["username"])
        wait.until(EC.visibility_of_element_located((By.XPATH, X_LOGIN_PASS))).send_keys(user["password"])
        wait_and_click(X_LOGIN_SUBMIT)
        time.sleep(1.5)  # pequeño respiro post-login

        print(f"➡️  [{name}] Ir a Retiros…")
        driver.get(WITHDRAW_URL)
        # espera a que al menos exista la tabla/listado
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//table|//tbody")))
        except TimeoutException:
            print(f"⚠️ [{name}] No se detectó tabla; continuando de todas formas.")

        # Señala que llegó y espera para arrancar a la vez
        ready_event.set()
        start_event.wait()

        for run in range(2):
            print(f"— [{name}] Iteración {run+1} —")

            # 1) checkbox primera fila (re-obtén cada iteración por si la tabla cambia)
            try:
                checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, X_FIRST_CHECK)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
                time.sleep(0.2)
                js_click(driver, checkbox)
            except StaleElementReferenceException:
                checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, X_FIRST_CHECK)))
                js_click(driver, checkbox)

            # 2) botón "Ejecutar"
            ejecutar_btn = wait_and_click(X_EJECUTAR_BTN)

            # 3) Acción = "Procesar en Lote"
            action_select = wait.until(EC.visibility_of_element_located((By.XPATH, X_ACTION_SEL)))
            Select(action_select).select_by_visible_text("Procesar en Lote")

            # 4) Banco = "BCI"
            bank_select = wait.until(EC.visibility_of_element_located((By.XPATH, X_BANK_SEL)))
            Select(bank_select).select_by_visible_text("BCI")

            # 5) Guardar
            wait_and_click(X_SAVE_BTN)

            # 6) Confirmaciones "Sí" (hasta 5 intentos por si aparece varias veces)
            for i in range(5):
                try:
                    yes_btn = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, X_CONFIRM_SI))
                    )
                    js_click(driver, yes_btn)
                    print(f"   [{name}] Confirmación {i+1}")
                    time.sleep(0.5)
                except TimeoutException:
                    # si ya no aparece más, rompemos el ciclo
                    break

            time.sleep(1.5)  # pequeña pausa entre iteraciones

        print(f"✅ [{name}] Flujo completado.")
        time.sleep(2)

    except Exception as e:
        print(f"❌ [{name}] Error:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    # modo seguro en Windows para multiprocessing
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    # dos eventos de “listo” + uno para arrancar sincronizado
    ready1, ready2 = Event(), Event()
    start_together = Event()

    p1 = Process(target=worker, args=(USERS[0], ready1, start_together, HEADLESS))
    p2 = Process(target=worker, args=(USERS[1], ready2, start_together, HEADLESS))

    p1.start(); p2.start()
    # espera a que ambos estén en la página de retiros
    ready1.wait(); ready2.wait()
    # liberar para empezar a ejecutar al mismo tiempo
    start_together.set()

    p1.join(); p2.join()
    print("🏁 Paralelo finalizado.")
