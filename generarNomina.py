#flujo seleccionar solicitud de retiro en bo2, ejecutar en lote, generar nómina, seleccionar banco procesar en lote 

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select 
from selenium.webdriver.support import expected_conditions as EC

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    # 1. Ir a la página de login y hacer login
    driver.get("https://backoffice-v2.qa.wcbackoffice.com/")
    driver.maximize_window() 
    user_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Usuario']")))
    user_field.send_keys("mcastro")
    pass_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Contraseña']")))
    pass_field.send_keys("N3wP@ssw0rd2024")
    ingresar_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Ingresar']")))
    ingresar_btn.click()
    
    time.sleep(3)  # Espera a que se procese el login

    # 2. Navegar a la página de Retiros
    driver.get("https://backoffice-v2.qa.wcbackoffice.com/admin/requests/withdrawal")
    time.sleep(3)
    
    # 3. Seleccionar el checkbox del primer retiro haciendo clic en su contenedor
    try:
        checkbox_container = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//tbody/tr[1]/td[1]/div[1]/label[1]/span[1]")
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox_container)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", checkbox_container)
        print("Checkbox container clickeado.")
    except Exception as e:
        print("Error al seleccionar el checkbox:", e)
        print("URL actual:", driver.current_url)
    
    # 4. Hacer clic en el botón "Ejecutar"
    try:
        ejecutar_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@class='btn btn-secondary float-end me-1 btn-inverse']")
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", ejecutar_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", ejecutar_btn)
        print("Botón 'Ejecutar' clickeado.")
    except Exception as e:
        print("Error al clicar el botón 'Ejecutar':", e)
    
    # 5. Seleccionar la opción "BCI Procesado en Lote"
    try:
        select_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//select[@name='bank']")))
        bank_select = Select(select_element)
        bank_select.select_by_visible_text("BCI Procesado en Lote")
        print("Opción 'BCI Procesado en Lote' seleccionada en la lista.")
    except Exception as e:
        print("Error al seleccionar la opción 'BCI Procesado en Lote':", e)
    
    # 6. Clic en el botón "Continuar"
    try:
        continuar_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@class='btn btn-secondary float-end me-1 btn-inverse']")
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", continuar_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", continuar_btn)
        print("Botón 'Continuar' clickeado.")
    except Exception as e:
        print("Error al clicar el botón 'Continuar':", e)
    
    # Espera final para observar el resultado
    time.sleep(20)
    driver.quit()

if __name__ == "__main__":
    main()
