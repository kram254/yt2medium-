import requests
import sys

def check_health(url):
    try:
        response = requests.get(f"{url}/", timeout=10)
        if response.status_code == 200:
            print(f"✓ App is healthy: {url}")
            return True
        else:
            print(f"✗ App returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = check_health(url)
    sys.exit(0 if success else 1)
