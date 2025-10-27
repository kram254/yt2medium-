import subprocess
import time
import requests
import sys
import os

print("=" * 60)
print("TESTING PRODUCTION CONFIGURATION")
print("=" * 60)

os.environ['FLASK_ENV'] = 'production'
os.environ['PORT'] = '8000'

print("\n[1] Starting app with Gunicorn...")
process = subprocess.Popen(
    ['gunicorn', '-c', 'gunicorn_config.py', 'app:app'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print("Waiting for server to start...")
time.sleep(5)

print("\n[2] Testing endpoints...")
base_url = "http://localhost:8000"

endpoints = [
    ('/', 'Home page'),
    ('/history', 'History page'),
    ('/analytics', 'Analytics page'),
]

all_passed = True

for endpoint, name in endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=10)
        if response.status_code == 200:
            print(f"  [OK] {name}: {response.status_code}")
        else:
            print(f"  [FAIL] {name}: {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        all_passed = False

print("\n[3] Stopping server...")
process.terminate()
process.wait()

print("\n" + "=" * 60)
if all_passed:
    print("ALL TESTS PASSED - Ready for production")
    print("=" * 60)
    sys.exit(0)
else:
    print("SOME TESTS FAILED - Fix issues before deploying")
    print("=" * 60)
    sys.exit(1)
