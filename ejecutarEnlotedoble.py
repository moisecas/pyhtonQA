#flujo dos veces solicitud de retiro


import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    # 1. Login
    driver.get("https://backoffice-v2.qa.wcbackoffice.com/")
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Usuario']"))).send_keys("mcastro")
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Contraseña']"))).send_keys("N3wP@ssw0rd2024")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Ingresar']"))).click()
    time.sleep(3)

    # 2. Navegar a Retiros
    driver.get("https://backoffice-v2.qa.wcbackoffice.com/admin/requests/withdrawal")
    time.sleep(3)

    # 3–8. Repetir el flujo de procesar la primera solicitud 2 veces
    for run in range(2):
        print(f"--- Iteración {run+1} ---")

        # 3. Seleccionar el checkbox de la primera fila
        checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[1]/td[1]/div/label/span")))
        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", checkbox)

        from selenium.common.exceptions import NoSuchElementException

        # 4. Clic en "Ejecutar"
        ejecutar_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class,'btn-inverse')]")
        ))
        driver.execute_script("arguments[0].click();", ejecutar_btn)

        # 5. Seleccionar acción: buscar por name EXACTO, por 'action' o por nombre que termine en '-action'
        action_select = wait.until(EC.visibility_of_element_located((
            By.XPATH,
            "//select[@name='5973-action']"
            " | //select[@name='action']"
            " | //select[substring(@name, string-length(@name)-7)='-action']"
        )))
        sel_action = Select(action_select)

        # Preferir "Procesar"; si no, probar "Procesar en Lote"; si tampoco, elegir la que contenga "Procesar"
        try:
            sel_action.select_by_visible_text("Procesar")
        except NoSuchElementException:
            try:
                sel_action.select_by_visible_text("Procesar en Lote")
            except NoSuchElementException:
                opts = [o.text.strip() for o in sel_action.options]
                print("Opciones de acción disponibles:", opts)
                clicked = False
                for o in sel_action.options:
                    if "Procesar" in o.text:
                        o.click()
                        clicked = True
                        break
                if not clicked:
                    raise

        # 5.1 Espera solicitada (habilita dependencias del formulario)
        time.sleep(5)

        # 6. Seleccionar banco "BCI"
        bank_select = wait.until(EC.visibility_of_element_located((By.XPATH, "//select[@name='bank']")))
        Select(bank_select).select_by_visible_text("BCI")

        # 7. Guardar (botón a la derecha)
        try:
            save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-primary float-end']")))
        except TimeoutException:
            save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'btn-primary') and contains(@class,'float-end')]")))
        driver.execute_script("arguments[0].click();", save_btn)

        # 8. Confirmar "Sí" si aparece (hasta 5 veces)
        for i in range(5):
            try:
                yes_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-danger' and normalize-space()='Sí']"))
                )
                driver.execute_script("arguments[0].click();", yes_btn)
                print(f"Confirmación {i+1}")
                time.sleep(0.4)
            except TimeoutException:
                break


    print("✅ Flujo completado dos veces.")
    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()
