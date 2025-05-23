#modulo retiro pero dando clic en el check de retirar todo el sado


import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Lista de jugadores
players = [
    "TEST_GM2", "test_dev_04", "DANIELTEST01"
]

# Valor de contraseña
fixed_password = "Cc12345678@@"

for player in players:
    print("Procesando usuario:", player)
    
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. Acceder a la página principal y maximizar
        driver.get("https://skin2-latamwin.qa.andes-system.com/")
        driver.maximize_window()
    
        # 2. Clic en "Ingresar"
        iniciar_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[@class='flex items-center justify-center gap-2 max-lg:hidden']"
            "//button[contains(normalize-space(),'Ingresar')]"
        )))
        iniciar_btn.click()
    
        # 3. Rellenar Usuario
        usuario_input = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//input[@placeholder='Usuario']"
        )))
        usuario_input.clear()
        usuario_input.send_keys(player)
    
        # 4. Rellenar Contraseña
        contrasena_input = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//input[@placeholder='Contraseña']"
        )))
        contrasena_input.clear()
        contrasena_input.send_keys(fixed_password)
    
        # 5. Clic en "Submit"
        submit_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@type='submit']"
        )))
        submit_btn.click()
    
        time.sleep(5)  # esperar a que termine el login
    
        # 6. Cerrar modal si aparece
        try:
            close_element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((
                By.XPATH,
                "//header[@class='flex items-baseline justify-between gap-5 py-5']//*[name()='svg']"
            )))
            close_element.click()
            print("Modal de cierre clickeado.")
        except:
            print("Modal de cierre no apareció.")
    
        # 7. Ir a withdrawals
        driver.get("https://skin2-latamwin.qa.andes-system.com/withdrawals")
        time.sleep(10)
    
        # 8. Clic en el checkbox específico de withdrawals
        try:
            withdrawal_checkbox = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//div[@class="flex items-center justify-center w-5 h-5 text-xs border rounded duration-300 '
                '[&>*]:opacity-0 before:content-[\'\'] before:absolute before:rounded-full before:w-9 before:h-9 '
                'before:z-[-1] before:opacity-0 before:transition-all before:duration-300 peer '
                'peer-checked:before:w-9 peer-checked:before:h-9 peer-checked:[&>*]:opacity-100 '
                'peer-disabled:before:hidden hover:before:opacity-100 peer-checked:hover:before:opacity-50 '
                'pressed:before:opacity-100 peer-checked:pressed:before:opacity-100 bg-transparent '
                'border-neutral-200 border rounded before:bg-neutral-100 before:w-9 before:h-9 '
                'peer-checked:before:bg-neutral-100 peer-disabled:border-neutral-200 peer-disabled:bg-neutral-100 '
                'peer-disabled:peer-checked:border-neutral-200 peer-disabled:peer-checked:bg-red-900 '
                'pressed:border-neutral-500"]//*[name()="svg"]'
            )))
            driver.execute_script("arguments[0].scrollIntoView(true);", withdrawal_checkbox)
            time.sleep(1)
            withdrawal_checkbox.click()
            print("Checkbox de withdrawals clickeado.")
        except Exception as e:
            print("No se pudo clicar el checkbox de withdrawals:", e)
    
    # 9. Clic en el botón final de submit para completar el retiro
        final_submit_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        final_submit_btn.click()
    
        print("Retiro procesado para:", player)
    
    except Exception as e:
        print("Error procesando el usuario", player, ":", e)
    
    # cerrar y pausar antes del siguiente
    time.sleep(5)
    driver.quit()
    time.sleep(2)
