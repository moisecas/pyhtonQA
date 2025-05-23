#retiro skin2 de un jugador según las variables de entorno 

import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main(): # Cargar variables de entorno desde .env
    load_dotenv()
    usuario = os.getenv("USUARIO")
    contrasena = os.getenv("CONTRASENA")
    monto = os.getenv("MONTO")
    
    driver = webdriver.Chrome()
    driver.get("https://skin2-latamwin.qa.andes-system.com/")
    driver.maximize_window() 

    wait = WebDriverWait(driver, 10)
    
    try: #clic en iniciar sesion
        iniciar_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Iniciar sesión']")))
        iniciar_btn.click()
        print("Clic en 'Iniciar sesión' realizado.")
    except Exception as e:
        print("Error al clicar en 'Iniciar sesión':", e)
    
    try:   #completar campos de usuario y contraseña
        usuario_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[contains(@placeholder,'Usuario')]")))
        usuario_input.clear()
        usuario_input.send_keys(usuario)
        print("Campo 'Usuario' completado.")
    except Exception as e:
        print("Error en el campo 'Usuario':", e)
    
    try:
        contrasena_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Contraseña']")))
        contrasena_input.clear()
        contrasena_input.send_keys(contrasena)
        print("Campo 'Contraseña' completado.")
    except Exception as e:
        print("Error en el campo 'Contraseña':", e)
    
    try: #clic en el boton de iniciar sesion
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        submit_btn.click()
        print("Clic en botón de submit (login) realizado.")
    except Exception as e:
        print("Error al clicar en el botón de submit:", e)
    time.sleep(10) # Espera de 10 segundos para que cargue la página  
    
    try: #navegar a la pagina de retiros 
        driver.get("https://skin2-latamwin.qa.andes-system.com/withdrawals")
        print("Navegación a 'Withdrawals' realizada.")
    except Exception as e:
        print("Error al navegar a 'Withdrawals':", e)   
    #time.sleep(5) # Espera de 5 segundos para que cargue la página

    try: #completar campo de monto
        monto_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Monto']")))
        monto_input.clear()
        monto_input.send_keys(monto)
        print("Campo 'Monto' completado.")
    except Exception as e:
        print("Error en el campo 'Monto':", e)
    
    
    try: #clic en el boton final soliciutd de retiro 
        final_submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        final_submit_btn.click()
        print("Clic en botón final de submit realizado.")
    except Exception as e:
        print("Error al clicar en el botón final de submit:", e)
    
    # Espera final de 5 segundos para observar el resultado
    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()