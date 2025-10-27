import subprocess
import sys

def run_command(cmd, description):
    print(f"\n[→] {description}")
    print(f"    Command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"    [OK] Success")
        if result.stdout:
            print(f"    Output: {result.stdout.strip()}")
        return True
    else:
        print(f"    [FAIL] Failed")
        if result.stderr:
            print(f"    Error: {result.stderr.strip()}")
        return False

print("=" * 70)
print("RENDER DEPLOYMENT AUTOMATION")
print("=" * 70)

print("\nStep 1: Pre-deployment check")
if not run_command("python pre_deploy_check.py", "Running pre-deployment checks"):
    print("\n[FAIL] Pre-deployment checks failed. Fix errors and try again.")
    sys.exit(1)

print("\nStep 2: Git operations")
run_command("git add .", "Adding all files to git")
run_command('git commit -m "Deploy to Render"', "Committing changes")

print("\nStep 3: Check remote repository")
result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
if "origin" in result.stdout:
    print("[OK] Git remote configured")
    print(result.stdout)
    
    push = input("\nPush to GitHub? (y/n): ")
    if push.lower() == 'y':
        run_command("git push origin main", "Pushing to GitHub")
else:
    print("[WARN] No git remote found")
    print("Add remote with: git remote add origin <your-repo-url>")

print("\n" + "=" * 70)
print("DEPLOYMENT INSTRUCTIONS FOR RENDER")
print("=" * 70)
print("""
1. Go to https://render.com/dashboard
2. Click 'New +' → 'Web Service'
3. Connect your GitHub repository
4. Configure:
   - Name: yt2medium
   - Environment: Python 3
   - Build Command: chmod +x build.sh && ./build.sh
   - Start Command: gunicorn -c gunicorn_config.py app:app
   - Instance Type: Free (or Starter)

5. Add Environment Variables (REQUIRED):
   - OPENAI_API_KEY=<your-key>
   - OPENROUTER_API_KEY=<your-key>
   - SECRET_KEY=<random-string>
   - FLASK_ENV=production

6. Optional Variables:
   - ANTHROPIC_API_KEY=<your-key>
   - SUPABASE_URL=<your-url>
   - SUPABASE_KEY=<your-key>

7. Click 'Create Web Service'
8. Wait 5-10 minutes for deployment
9. Access your app at: https://yt2medium.onrender.com
""")

print("=" * 70)
print("DEPLOYMENT PREPARED")
print("=" * 70)
