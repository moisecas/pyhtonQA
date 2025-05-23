from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Lista de correos para login
# emails = [
#     "gmunoz@promarketingchile.com",
#     "mauchacon94429@gmail.com",
#     "maiev740@gmail.com",
#     "echacon1@promarketingchile.com"
# ]

emails = [
   "TEST_GM", "test_dev_0", "DANIELTEST0"
]



fixed_password = "Cc12345678@@" #ahora por el user mal y pass bien 

# Aquí iremos guardando el estado de cada intento
results = []

for email in emails:
    status = "OK"
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    try:
        driver.get("https://skin2-latamwin.qa.andes-system.com/")
        driver.maximize_window()

        iniciar_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[@class='flex items-center justify-center gap-2 max-lg:hidden']"
            "//button[contains(normalize-space(),'Ingresar')]"
        )))
        iniciar_btn.click()

        user_input = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//input[@placeholder='Usuario']"
        )))
        user_input.clear()
        user_input.send_keys(email)

        pwd_input = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//input[@placeholder='Contraseña']"
        )))
        pwd_input.clear()
        pwd_input.send_keys(fixed_password)

        submit_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@type='submit']"
        )))
        submit_btn.click()

        # Aquí podrías añadir un check concreto de éxito,
        # p.ej. esperar a que aparezca un elemento de dashboard
        time.sleep(10)

    except Exception as e:
        status = f"ERROR: {e.__class__.__name__}"
    finally:
        driver.quit()

    results.append({
        "email": email,
        "status": status,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# Generación de HTML usando f-string (Opción B)
date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte de Logins</title>
  <style>
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #eee; }}
    .OK {{ background: #cfc; }}
    .ERROR {{ background: #fcc; }}
  </style>
</head>
<body>
  <h1>Reporte de Logins - {date_str}</h1>
  <table>
    <thead>
      <tr><th>Email</th><th>Resultado</th><th>Timestamp</th></tr>
    </thead>
    <tbody>
"""

for r in results:
    cls = "OK" if r["status"] == "OK" else "ERROR"
    html += (
        f"      <tr class='{cls}'>"
        f"<td>{r['email']}</td><td>{r['status']}</td><td>{r['timestamp']}</td>"
        "</tr>\n"
    )

html += """    </tbody>
  </table>
</body>
</html>
"""

with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Reporte HTML generado en report.html")
