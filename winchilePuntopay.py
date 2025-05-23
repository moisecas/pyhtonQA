import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    # 1. Abrir página e iniciar login
    driver.get("https://winchile.dev.wcbackoffice.com/")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='theme-btn loginModalBtn']"))).click()
    time.sleep(10) 

    # 2. Rellenar usuario y contraseña (reemplaza con tus credenciales)
    user_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='username']")))
    user_input.send_keys("TEST_WINS")
    pass_input = driver.find_element(By.XPATH, "//input[@name='password']")
    pass_input.send_keys("N3wP@ssw0rd2024")
    time.sleep(5)  
    
    # 3. Enviar login
    driver.find_element(
    By.XPATH,
    '//button[@class="theme-btn noAction" and @onclick="processLogin();" and normalize-space()="INGRESAR"]').click()
    time.sleep(10)  # esperar a que cargue el sitio

    # 4. Ir a Deposit
    driver.get("https://winchile.dev.wcbackoffice.com/deposit")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//img[@src='/images/puntopay.png']"))).click()

    # 5. Escribir monto en modal y avanzar
    amount_input = wait.until(
    EC.visibility_of_element_located((By.XPATH, "//input[@id='amount']")))

    amount_input.clear()
    amount_input.send_keys("10000")
    driver.find_element(By.XPATH, "//button[@id='chargeButtom']").click()

    time.sleep(5)

    # 6. Seleccionar método de pago
    wait.until(
    EC.element_to_be_clickable((By.XPATH, "//button[@id='button_payment']"))
).click()

    # Seleccionar tarjeta
    wait.until(
    EC.element_to_be_clickable((By.XPATH, "//button[@id='tarjetas']"))
).click() 
    time.sleep(20)
    # # 7. Completar datos de la tarjeta
    # wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@id='card-number']"))).send_keys("4051885600446623")
    # time.sleep(25)
    
    # driver.find_element(By.XPATH, "//input[@id='card-exp']").send_keys("1030")
    # time.sleep(5)
    # driver.find_element(By.XPATH, "//input[@id='card-cvv']").send_keys("123")
    # time.sleep(5)
    # driver.find_element(By.XPATH, "//button[normalize-space()='Continuar']").click()

    # — justo después de seleccionar tu método de pago —
# 6. Cambiar al iframe que contiene el formulario de tarjeta
    wait.until(EC.frame_to_be_available_and_switch_to_it(
    (By.CSS_SELECTOR, "iframe[src*='puntopay']")  # ajusta el selector si cambia
))

    # 7. Ahora ya puedes localizar los campos dentro del iframe:
    wait.until(EC.visibility_of_element_located((By.ID, "card-number"))).send_keys("4051885600446623")
    wait.until(EC.visibility_of_element_located((By.ID, "card-exp"))).send_keys("1030")
    wait.until(EC.visibility_of_element_located((By.ID, "card-cvv"))).send_keys("123")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continuar']"))).click()

    # 8. Salir del iframe para continuar con el flujo principal:
    driver.switch_to.default_content()


    driver.find_element(By.XPATH, "//button[normalize-space()='Pagar']").click()
    time.sleep(8)

    # 8. Completar datos de cliente en el iframe/modal
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@id='rutClient']"))).send_keys("11111111-1")
    driver.find_element(By.XPATH, "//input[@id='passwordClient']").send_keys("123")
    driver.find_element(By.XPATH, "//input[@value='Aceptar']").click()
    driver.find_element(By.XPATH, "//input[@value='Continuar']").click()
    time.sleep(20)

    # 9. Redirigir y validar éxito
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@id='redirect_result_btn']"))).click()
    success = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//p[normalize-space()='Transacción Exitosa']")
    ))
    if success:
        print("✅ Transacción Exitosa encontrada")
    else:
        print("❌ No se encontró el mensaje de éxito")

    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()