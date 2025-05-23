import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL = "https://backoffice-v2.qa.wcbackoffice.com/"
WITHDRAWAL_URL = "https://backoffice-v2.qa.wcbackoffice.com/admin/requests/withdrawal"
USERNAME = "mcastro"
PASSWORD = "N3wP@ssw0rd2024"

def process_flow(instance_num):
    print(f"[Instancia {instance_num}] Iniciando flujo")
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    try:
        # 1. Login
        driver.get(LOGIN_URL)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Usuario']"))).send_keys(USERNAME)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Contraseña']"))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Ingresar']"))).click()
        time.sleep(3)

        # 2. Ir a Retiros
        driver.get(WITHDRAWAL_URL)
        time.sleep(3)

        # 3. Seleccionar las dos primeras solicitudes
        checkboxes = wait.until(EC.presence_of_all_elements_located((
            By.XPATH, "//tbody/tr[position()<=2]/td[1]/div/label/span"
        )))
        for cb in checkboxes:
            driver.execute_script("arguments[0].scrollIntoView(true);", cb)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", cb)
        print(f"[Instancia {instance_num}] Seleccionadas {len(checkboxes)} solicitudes")

        # 4. Clic en "Ejecutar"
        ejecutar_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(@class,'btn-inverse')]"
        )))
        driver.execute_script("arguments[0].click();", ejecutar_btn)

        # 5. Seleccionar "Procesar"
        action_select = wait.until(EC.visibility_of_element_located((By.XPATH, "//select[@name='action']")))
        Select(action_select).select_by_visible_text("Procesar")

        # 6. Seleccionar "Banco de Chile"
        bank_select = wait.until(EC.visibility_of_element_located((By.XPATH, "//select[@name='bank']")))
        Select(bank_select).select_by_visible_text("Banco de Chile")

        # 7. Clic en "Guardar"
        save_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@type='submit' and contains(@class,'btn-primary')]"
        )))
        driver.execute_script("arguments[0].click();", save_btn)

        # 8. Pulsar “Sí” 5 veces, relocalizando el botón en cada iteración
        clicks = 0
        for i in range(5):
            yes_btn = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[@class='btn btn-danger' and normalize-space()='Sí']"
            )))
            driver.execute_script("arguments[0].click();", yes_btn)
            clicks += 1
            print(f"[Instancia {instance_num}] Confirmación {clicks}")
            time.sleep(0.5)

        print(f"[Instancia {instance_num}] Flujo completado con {clicks} confirmaciones")
        time.sleep(2)

    except Exception as e:
        print(f"[Instancia {instance_num}] Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    threads = []
    for i in range(2):  # Lanzar dos navegadores concurrentes
        t = threading.Thread(target=process_flow, args=(i+1,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("✅ Ambos flujos completados.")
