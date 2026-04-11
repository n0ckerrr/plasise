import requests
import sys

def test_url(url, name):
    try:
        print(f"Testing {name}: {url} ...", flush=True)
        r = requests.get(url, timeout=10)
        print(f"[{r.status_code}] {name}")
        if r.status_code == 200:
            print(f"Body: {r.text[:200]}")
            return True
        else:
            print(f"ERROR Body: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"EXCEPTION {name}: {e}")
        return False

base = 'http://127.0.0.1:5000'

# Test 1: Session (v1)
ok1 = test_url(f"{base}/api/v1/auth/session", "Session V1")

# Test 2: Products (v1)
ok2 = test_url(f"{base}/api/v1/products?per_page=1", "Products V1")

# Test 3: Session (Legacy)
ok3 = test_url(f"{base}/api/session", "Session Legacy")

# Test 4: Products (Legacy)
ok4 = test_url(f"{base}/api/productos", "Products Legacy")

if ok1 and ok2 and ok3 and ok4:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
