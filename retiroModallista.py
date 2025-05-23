#generar retiros del skin2 para 26 jugadores mapeando el modal q se abre para cerrarlo 

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

# Valor de contraseña 
fixed_password = "Cc12345678@@"

for player in players:
    print("Procesando usuario:", player)
    
    # Inicia el navegador
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. Acceder a la página principal y maximizar ventana
        driver.get("https://skin2-latamwin.qa.andes-system.com/")
        driver.maximize_window()
    
        # 2. Clic en "Iniciar sesión"
        iniciar_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='flex items-center justify-center gap-2 max-lg:hidden']//button[@class='uppercase text-button-sing-in-text text-sm font-bold border border-neutral-100 transition-colors hover:bg-button-sing-in-hover hover:border-button-sing-in-hover font-serif flex items-center whitespace-nowrap leading-4 h-8 px-4 py-2 rounded-lg lg:text-xl lg:h-auto lg:leading-6'][normalize-space()='Ingresar']"))
        )
        iniciar_btn.click()
    
        # 3. Escribir en el campo de Usuario
        usuario_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Usuario']"))
        )
        usuario_input.clear()
        usuario_input.send_keys(player)
    
        # 4. Escribir en el campo de Contraseña
        contrasena_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Contraseña']"))
        )
        contrasena_input.clear()
        contrasena_input.send_keys(fixed_password)
    
        # 5. Clic en el botón submit para iniciar sesión
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        submit_btn.click()
    
        # Esperar a que se inicie sesión (ajusta el tiempo según necesidad)
        time.sleep(5)
    
        # Validar si se presenta el elemento de cierre (por ejemplo, un modal o notificación)
        try:
            close_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//header[@class='flex items-baseline justify-between gap-5 py-5']//*[name()='svg']"))
            )
            close_element.click()
            print("Elemento de cierre encontrado y clickeado.")
        except Exception as e:
            print("Elemento de cierre no encontrado, continuando...")
    
        # 6. Navegar directamente a la página de Retiros
        driver.get("https://skin2-latamwin.qa.andes-system.com/withdrawals")
    
        # Esperar a que la página de Retiros cargue
        time.sleep(10)
        # 7. Escribir el monto (ejemplo: 1000)
        monto_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Monto']"))
        )
        monto_input.clear()
        monto_input.send_keys("1000") #solicitud de retiro con 00
    
        # 8. Clic en el botón final de submit para completar el retiro
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
