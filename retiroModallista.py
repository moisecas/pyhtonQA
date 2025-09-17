#generar retiros del skin2 para 26 jugadores mapeando el modal q se abre para cerrarlo 

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Lista de jugadores
players = [
  "test_dev_04", "YOYDEV", "CRIS_QA", "BONO_BO", "TEST_VERIFICACION_CORREO",
  "HILLSONG", "TESTBONUS_SK2", "TESTINGQA", "TEST.REGISTRO", "TESTSKIN2_7", "TEST_NOTIFICACIONES", "TEST_AUTOLIMITACIONES",
  "TEST_GM5", 
  "nuevo_usuario_02", "nuevo_usuario_01", "nuevo_usuario_03", "nuevo_usuario_04", "nuevo_usuario_05",
  "nuevo_usuario_06", "nuevo_usuario_07", "nuevo_usuario_08", "nuevo_usuario_09", "nuevo_usuario_10", "nuevo_usuario_11",
  "nuevo_usuario_12",  "nuevo_usuario_13",  "nuevo_usuario_14",  "nuevo_usuario_15",  "nuevo_usuario_16",  "nuevo_usuario_17",
  "nuevo_usuario_18",  "nuevo_usuario_19",  "nuevo_usuario_20",  "nuevo_usuario_21",  "nuevo_usuario_22",  "nuevo_usuario_23",
  "nuevo_usuario_24",  "nuevo_usuario_25",  "nuevo_usuario_26",  "nuevo_usuario_27",  "nuevo_usuario_28",  "nuevo_usuario_29",
  "nuevo_usuario_30", "nuevo_usuario_31",  "nuevo_usuario_32",  "nuevo_usuario_33",  "nuevo_usuario_34",  "nuevo_usuario_35",
    "nuevo_usuario_36",  "nuevo_usuario_37",  "nuevo_usuario_38",  "nuevo_usuario_39",  "nuevo_usuario_40",  "nuevo_usuario_41",
    "nuevo_usuario_50","nuevo_usuario_52","nuevo_usuario_53","nuevo_usuario_54","nuevo_usuario_55","nuevo_usuario_59",
  "nuevo_usuario_60","nuevo_usuario_61","nuevo_usuario_62","nuevo_usuario_63","nuevo_usuario_64","nuevo_usuario_65",
  "nuevo_usuario_66","nuevo_usuario_67","nuevo_usuario_70","nuevo_usuario_71","nuevo_usuario_72","nuevo_usuario_73","nuevo_usuario_74"
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
        driver.get("https://skin2-latamwin.dev.andes-system.com/")
        driver.maximize_window()
    
        # 2. Clic en "Iniciar sesión"
        iniciar_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'flex items-center justify-center gap-2 max-lg:hidden')]//button[contains(@class,'shadow shadow-black hover:bg-revamp-primary-fill-hover sm:hover:bg-none pressed:bg-revamp-primary-fill-pressed')][normalize-space()='Ingresar']"))
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
        driver.get("https://skin2-latamwin.dev.andes-system.com/?cashier=withdrawals")

        #time.sleep(15)

        #escoger xpath //div[@class='flex w-11/12 flex-nowrap gap-2']
        time.sleep(5)
        withdrawal_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='flex w-11/12 flex-nowrap gap-2']"))
        )
        withdrawal_option.click() # Clic en la opción de retiro bancario 

       

    
        # Esperar a que la página de Retiros cargue
        time.sleep(5)
        # 7. Escribir el monto (ejemplo: 1000)
        monto_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Min: $1.000 · Max: $100.000.000']"))
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
