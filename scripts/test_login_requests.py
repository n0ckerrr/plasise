import requests
import re

LOGIN_URL = "https://www.ibdglobal.com/web/login"
USERNAME = "plasiserosas@outlook.com"
PASSWORDS = ["M1l3ibd", "M1l3ibd."]

def test_login_with_password(password):
    print(f"Testing password: '{password}'")
    try:
        session = requests.Session()
        r = session.get(LOGIN_URL)
        print(f"  GET {LOGIN_URL} -> {r.status_code}")
        
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
        if not csrf_match:
            print("  Failed to find CSRF token")
            return False
        
        token = csrf_match.group(1)
        print(f"  CSRF: {token[:10]}...")
        
        login_data = {
            'login': USERNAME,
            'password': password,
            'csrf_token': token,
            'redirect': ''
        }
        
        r = session.post(LOGIN_URL, data=login_data)
        print(f"  POST Response URL: {r.url}")
        print(f"  Status: {r.status_code}")
        
        if "web/login" not in r.url:
            print(f"  SUCCESS! url={r.url}")
            return True
        else:
            print("  FAILED (still on login page)")
            return False
            
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    for pwd in PASSWORDS:
        if test_login_with_password(pwd):
            break
