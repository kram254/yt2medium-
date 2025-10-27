import os
import sys
from pathlib import Path

print("=" * 60)
print("PRE-DEPLOYMENT CHECK")
print("=" * 60)

errors = []
warnings = []
checks_passed = 0

print("\n[1] Checking required files...")
required_files = [
    'app.py',
    'requirements.txt',
    'build.sh',
    'gunicorn_config.py',
    'render.yaml',
    'runtime.txt',
    'Procfile',
    '.gitignore'
]

for file in required_files:
    if Path(file).exists():
        print(f"  [OK] {file}")
        checks_passed += 1
    else:
        print(f"  [FAIL] {file} missing")
        errors.append(f"Missing file: {file}")

print("\n[2] Checking environment variables...")
env_file = Path('.env')
if env_file.exists():
    print(f"  [OK] .env file exists")
    checks_passed += 1
    
    with open('.env', 'r') as f:
        content = f.read()
        
    critical_vars = ['OPENAI_API_KEY', 'OPENROUTER_API_KEY', 'SECRET_KEY']
    for var in critical_vars:
        if var in content and 'your-' not in content.split(var)[1].split('\n')[0]:
            print(f"  [OK] {var} is set")
            checks_passed += 1
        else:
            print(f"  [WARN] {var} needs configuration")
            warnings.append(f"Configure {var} in Render dashboard")
else:
    print(f"  [WARN] .env file not found (configure in Render)")
    warnings.append("Add environment variables in Render dashboard")

print("\n[3] Checking Python modules...")
try:
    import flask
    print(f"  [OK] Flask {flask.__version__}")
    checks_passed += 1
except:
    print(f"  [FAIL] Flask not installed")
    errors.append("Run: pip install -r requirements.txt")

try:
    import gunicorn
    print(f"  [OK] Gunicorn installed")
    checks_passed += 1
except:
    print(f"  [FAIL] Gunicorn not installed")
    errors.append("Run: pip install gunicorn")

print("\n[4] Checking app.py configuration...")
try:
    with open('app.py', 'r') as f:
        app_content = f.read()
        
    if "app = Flask(__name__)" in app_content:
        print(f"  [OK] Flask app initialized")
        checks_passed += 1
    else:
        print(f"  [FAIL] Flask app not found")
        errors.append("Flask app initialization missing")
        
    if "from medium_research_agent import" in app_content:
        print(f"  [OK] Medium research agent imported")
        checks_passed += 1
    else:
        print(f"  [WARN] Medium research agent not imported")
        warnings.append("Medium research agent may not be integrated")
        
except Exception as e:
    print(f"  [FAIL] Cannot read app.py: {e}")
    errors.append(str(e))

print("\n[5] Checking directory structure...")
if Path('templates').exists():
    print(f"  [OK] templates/ directory exists")
    checks_passed += 1
else:
    print(f"  [FAIL] templates/ directory missing")
    errors.append("Missing templates directory")

if Path('static').exists():
    print(f"  [OK] static/ directory exists")
    checks_passed += 1
else:
    print(f"  [WARN] static/ directory missing")
    warnings.append("Static files may not work")

print("\n[6] Checking Git repository...")
if Path('.git').exists():
    print(f"  [OK] Git repository initialized")
    checks_passed += 1
else:
    print(f"  [FAIL] Not a Git repository")
    errors.append("Run: git init")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Checks passed: {checks_passed}")
print(f"Warnings: {len(warnings)}")
print(f"Errors: {len(errors)}")

if warnings:
    print("\nWARNINGS:")
    for w in warnings:
        print(f"  - {w}")

if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  - {e}")
    print("\n[FAIL] Fix errors before deploying")
    sys.exit(1)
else:
    print("\n[OK] Ready to deploy to Render!")
    print("\nNext steps:")
    print("1. git add .")
    print("2. git commit -m 'Deploy to Render'")
    print("3. git push origin main")
    print("4. Create Web Service on Render.com")
    sys.exit(0)
