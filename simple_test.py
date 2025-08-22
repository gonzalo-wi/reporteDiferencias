import requests

try:
    # Probar conectividad básica
    print("Probando conectividad con 192.168.0.250:8001...")
    response = requests.get("http://192.168.0.250:8001", timeout=5)
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

try:
    # Probar endpoint específico
    print("Probando endpoint de diferencias...")
    url = "http://192.168.0.250:8001/api/reports/differences"
    params = {"desde": "2025-08-21", "hasta": "2025-08-21"}
    response = requests.get(url, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Datos recibidos: {len(data)} items")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
