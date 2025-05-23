import sys
import requests

BASE_URL = "https://credivivaapi.com"

CLIENTE_ID = 123
ESTADOS_VALIDOS = ["activo", "moroso", "suspendido"]


def validate_cliente(cliente_id): # Validar cliente primer para ver si existe
    url = f"{BASE_URL}/clientes/{cliente_id}"
    resp = requests.get(url)
    assert resp.status_code == 200, f"GET {url} devolvió {resp.status_code}, esperaba 200"
    data = resp.json()
    assert "email" in data, f"En la respuesta no existe la clave 'email': {data}"
    estado = data.get("estado")
    assert estado in ESTADOS_VALIDOS, f"estado '{estado}' no está en {ESTADOS_VALIDOS}"
    print(f"✅ /clientes/{cliente_id} OK")


def validate_creditos(cliente_id): # Validar créditos del cliente 
    url = f"{BASE_URL}/clientes/{cliente_id}/creditos"
    resp = requests.get(url)
    assert resp.status_code == 200, f"GET {url} devolvió {resp.status_code}, esperaba 200"
    data = resp.json()
    assert isinstance(data, list), f"Esperaba lista de créditos, vino: {type(data).__name__}"
    print(f"✅ /clientes/{cliente_id}/creditos OK")


def main(): # Función principal para ejecutar las validaciones 
    try:
        validate_cliente(CLIENTE_ID) # Validar cliente
        validate_creditos(CLIENTE_ID) # Validar créditos
    except AssertionError as e:
        print("❌ TEST FAILED:", e) #capturar error mostroar por consola
        sys.exit(1)
    print("🎉 TODOS LOS TESTS PASARON") #rta por consola 


if __name__ == "__main__":
    main()
