#!/usr/bin/env python3
"""
Script de prueba para verificar conectividad con la API externa
"""

import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def test_external_api():
    """Probar conectividad con la API externa"""
    base_url = os.getenv("EXTERNAL_APP_URL", "http://192.168.0.250:8001")
    endpoint = "/api/reports/differences"
    
    # Fecha de ayer
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    url = f"{base_url}{endpoint}"
    params = {
        "desde": yesterday,
        "hasta": yesterday
    }
    
    print(f"🔍 Probando conectividad...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print("-" * 50)
    
    try:
        print("⏳ Haciendo petición...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Datos recibidos: {len(data) if isinstance(data, list) else 'Object'}")
            print(f"📄 Primeros datos:")
            if isinstance(data, list) and len(data) > 0:
                print(f"   {data[0]}")
            elif isinstance(data, dict):
                print(f"   {data}")
            else:
                print(f"   {data}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_health():
    """Probar endpoint de salud local"""
    print("\n🏥 Probando health check local...")
    try:
        response = requests.get("http://localhost:8009/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error en health check: {e}")

if __name__ == "__main__":
    test_health()
    test_external_api()
