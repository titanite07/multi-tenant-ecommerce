import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_e2e_workflow():
    print("=" * 50)
    print("E2E WORKFLOW TEST")
    print("=" * 50)
    
    print("\n[1] Health Check")
    r = requests.get(f"{BASE_URL}/health/")
    print(f"    Status: {r.status_code}")
    print(f"    Response: {r.json()}")
    
    print("\n[2] API Root")
    r = requests.get(f"{BASE_URL}/")
    print(f"    Status: {r.status_code}")
    print(f"    Message: {r.json().get('message', 'N/A')}")
    
    print("\n[3] Register User")
    r = requests.post(f"{BASE_URL}/api/register/", json={
        "username": "e2euser",
        "email": "e2e@test.com",
        "password": "TestPass123",
        "role": "customer"
    })
    print(f"    Status: {r.status_code}")
    if r.status_code == 201:
        print(f"    User created: {r.json().get('username', 'N/A')}")
    else:
        print(f"    Response: {r.text[:100]}")
    
    print("\n[4] Login (Get Token)")
    r = requests.post(f"{BASE_URL}/api/token/", json={
        "username": "testadmin",
        "password": "testpass123"
    })
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        token = r.json().get("access")
        refresh = r.json().get("refresh")
        print(f"    Token received: {token[:30]}...")
    else:
        print(f"    Response: {r.text[:100]}")
        print("\n    Using superuser credentials...")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n[5] Get Products")
    r = requests.get(f"{BASE_URL}/api/products/", headers=headers)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = data.get("count", len(data.get("results", [])))
        print(f"    Products count: {count}")
    else:
        print(f"    Response: {r.text[:100]}")
    
    print("\n[6] Get Orders")
    r = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = data.get("count", len(data.get("results", [])))
        print(f"    Orders count: {count}")
    else:
        print(f"    Response: {r.text[:100]}")
    
    print("\n[7] Get Categories")
    r = requests.get(f"{BASE_URL}/api/categories/", headers=headers)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = data.get("count", len(data.get("results", [])))
        print(f"    Categories count: {count}")
    else:
        print(f"    Response: {r.text[:100]}")
    
    print("\n[8] Get Dashboard")
    r = requests.get(f"{BASE_URL}/api/dashboard/", headers=headers)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"    Total Products: {data.get('total_products', 'N/A')}")
        print(f"    Total Orders: {data.get('total_orders', 'N/A')}")
        print(f"    Total Revenue: {data.get('total_revenue', 'N/A')}")
    else:
        print(f"    Response: {r.text[:100]}")
    
    print("\n[9] Get My Cart")
    r = requests.get(f"{BASE_URL}/api/cart/my_cart/", headers=headers)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"    Cart total: {data.get('total', 'N/A')}")
    else:
        print(f"    Response: {r.text[:100]}")
    
    print("\n[10] Logout (Token Blacklist)")
    r = requests.post(f"{BASE_URL}/api/logout/", headers=headers, json={"refresh": refresh})
    print(f"    Status: {r.status_code}")
    print(f"    Response: {r.json()}")
    
    print("\n" + "=" * 50)
    print("E2E WORKFLOW TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    test_e2e_workflow()
