import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Lista de jugadores
players = [
    "TEST_GM2", "test_dev_04", "DANIELTEST01", "TESTSKIN2_1", "SWAGGER", "YOYDEV",
    "darling_qa2", "juaquina", "yexibel", "Carlos", "Carlos1", "e2fm", "daniel740",
    "pruebacorreo", "Anav", "MANUEL", "Marvin", "BONO_BO", "TEST_VERIFICACION_CORREO",
    "HILLSONG", "TESTBONUS_SK2", "TESTINGQA", "TEST.REGISTRO", "TESTSKIN2_7",
    "TEST_NOTIFICACIONES", "TEST_AUTOLIMITACIONES"
]

# Valor de contraseña (puedes modificarlo o incluso tener una lógica para cada jugador)
fixed_password = "Cc12345678@@"

for player in players:
    print("Procesando usuario:", player)
    
    # Inicia el navegador
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. Acceder a la página principal
        driver.get("https://skin2-latamwin.qa.andes-system.com/")
        driver.maximize_window() 
    
        # 2. Click en "Iniciar sesión"
        iniciar_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Iniciar sesión']"))
        )
        iniciar_btn.click()
    
        # 3. Escribir en el campo de Usuario
        usuario_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[contains(@placeholder,'Usuario')]"))
        )
        usuario_input.clear()
        usuario_input.send_keys(player)
    
        # 4. Escribir en el campo de Contraseña
        contrasena_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Contraseña']"))
        )
        contrasena_input.clear()
        contrasena_input.send_keys(fixed_password)
    
        # 5. Click en el botón submit para iniciar sesión
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        submit_btn.click()
    
        # Esperar a que se inicie sesión (ajusta el tiempo según necesidad)
        time.sleep(3)
    
        # 6. Navegar directamente a la página de Retiros
        driver.get("https://skin2-latamwin.qa.andes-system.com/withdrawals")
    
        # 7. Escribir el monto (ejemplo: 1000)
        monto_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Monto']"))
        )
        monto_input.clear()
        monto_input.send_keys("1000")
    
        # 8. Click en el botón final de submit para completar el retiro
        final_submit_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        final_submit_btn.click()
    
        print("Retiro procesado para:", player)
    
    except Exception as e:
        print("Error procesando el usuario", player, ":", e)
    
    # Espera 5 segundos para observar el resultado y cierra el navegador
    time.sleep(5)
    driver.quit()
    
    # Breve pausa entre iteraciones
    time.sleep(2)
