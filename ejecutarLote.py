#multiples clics sobre el modal de confirmación 

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    # 1. Login…
    driver.get("https://backoffice-v2.qa.wcbackoffice.com/")
   
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Usuario']"))).send_keys("mcastro")
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Contraseña']"))).send_keys("N3wP@ssw0rd2024")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Ingresar']"))).click()
    time.sleep(3)

    # 2. Ir a Retiros…
    driver.get("https://backoffice-v2.qa.wcbackoffice.com/admin/requests/withdrawal")
    time.sleep(3)

    # 3. Seleccionar checkbox…
    checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[1]/td[1]/div/label/span")))
    driver.execute_script("arguments[0].click();", checkbox)

    # 4. Ejecutar…
    ejecutar_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'btn-inverse')]")))
    driver.execute_script("arguments[0].click();", ejecutar_btn)

    # 5. Seleccionar Procesar…
    Select(wait.until(EC.visibility_of_element_located((By.XPATH, "//select[@name='action']")))).select_by_visible_text("Procesar")
    # 6. Seleccionar Banco de Chile…
    Select(wait.until(EC.visibility_of_element_located((By.XPATH, "//select[@name='bank']")))).select_by_visible_text("Banco de Chile")
        # 7. Clic en "Guardar"
    save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(@class,'btn-primary')]")))
    driver.execute_script("arguments[0].click();", save_btn)

    # 8. Pulsar “Sí” 5 veces seguidas
    yes_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[@class='btn btn-danger' and normalize-space()='Sí']"
    )))
    for i in range(5):
        driver.execute_script("arguments[0].click();", yes_btn)
        print(f"Clic {i+1}: botón 'Sí' pulsado.")
        time.sleep(1)

    # 9. Cierre y fin
    print("✅ Se realizaron 5 clics de confirmación.")
    time.sleep(5)
    driver.quit()


if __name__ == "__main__":
    main()
