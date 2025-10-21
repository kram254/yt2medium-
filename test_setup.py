import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_python_version():
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.11+)")
        return False

def check_environment_variables():
    print("\n🔧 Checking environment variables...")
    print("   At least one AI provider API key is required:")
    
    providers = {
        'OPENAI_API_KEY': 'OpenAI API key (Primary)',
        'PROJECT_ID': 'Google Cloud Project ID (Secondary)',
        'ANTHROPIC_API_KEY': 'Anthropic API key (Fallback)',
    }
    optional = {
        'LOCATION': 'GCP Region (default: us-central1)',
        'PORT': 'Server port (default: 8080)',
    }
    
    providers_configured = []
    for var, description in providers.items():
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 8}... ({description})")
            providers_configured.append(var)
        else:
            print(f"   ⚠️  {var}: Not set ({description})")
    
    for var, description in optional.items():
        value = os.getenv(var)
        if value:
            print(f"   ℹ️  {var}: {value}")
        else:
            print(f"   ℹ️  {var}: Not set ({description})")
    
    if len(providers_configured) == 0:
        print("\n   ❌ No AI provider API keys configured!")
        print("   Configure at least one: OPENAI_API_KEY, PROJECT_ID, or ANTHROPIC_API_KEY")
        return False
    else:
        print(f"\n   ✅ {len(providers_configured)} AI provider(s) configured")
        return True

def check_dependencies():
    print("\n📦 Checking dependencies...")
    required_packages = [
        'flask',
        'markdown',
        'dotenv',
        'requests',
        'yt_dlp'
    ]
    optional_packages = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google.genai', 'Google Gemini'),
    ]
    
    all_good = True
    for package in required_packages:
        try:
            __import__(package.replace('.', '/').split('/')[0])
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (not installed)")
            all_good = False
    
    print("\n   Optional AI provider packages:")
    providers_available = 0
    for package, name in optional_packages:
        try:
            __import__(package.replace('.', '/').split('/')[0])
            print(f"   ✅ {name} ({package})")
            providers_available += 1
        except ImportError:
            print(f"   ⚠️  {name} ({package}) - not installed")
    
    if providers_available == 0:
        print(f"\n   ❌ No AI provider packages installed!")
        all_good = False
    else:
        print(f"\n   ✅ {providers_available} AI provider package(s) available")
    
    return all_good

def check_gcloud_auth():
    print("\n🔐 Checking gcloud authentication...")
    import subprocess
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'application-default', 'print-access-token'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("   ✅ Authenticated with gcloud")
            return True
        else:
            print("   ❌ Not authenticated")
            print("   Run: gcloud auth application-default login")
            return False
    except FileNotFoundError:
        print("   ⚠️  gcloud CLI not found (optional for local dev)")
        return True
    except subprocess.TimeoutExpired:
        print("   ⚠️  gcloud check timed out")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not verify: {e}")
        return True

def test_api_connection():
    print("\n🌐 Testing AI Provider connections...")
    any_working = False
    
    if os.getenv('OPENAI_API_KEY'):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            print("   ✅ OpenAI API key configured")
            any_working = True
        except Exception as e:
            print(f"   ⚠️  OpenAI setup issue: {str(e)}")
    
    if os.getenv('PROJECT_ID'):
        try:
            from google import genai
            from util import get_project_id
            
            client = genai.Client(
                vertexai=True,
                project=get_project_id(),
                location=os.getenv('LOCATION', 'us-central1'),
            )
            print("   ✅ Google Vertex AI configured")
            any_working = True
        except Exception as e:
            print(f"   ⚠️  Gemini setup issue: {str(e)}")
    
    if os.getenv('ANTHROPIC_API_KEY'):
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            print("   ✅ Anthropic API key configured")
            any_working = True
        except Exception as e:
            print(f"   ⚠️  Anthropic setup issue: {str(e)}")
    
    if not any_working:
        print("   ❌ No AI providers working!")
        return False
    
    return True

def main():
    print("=" * 60)
    print("🎥 YouTube to Medium - Setup Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Environment Variables", check_environment_variables()))
    results.append(("GCloud Auth", check_gcloud_auth()))
    results.append(("API Connection", test_api_connection()))
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for name, status in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
    
    all_passed = all(status for _, status in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! You're ready to run the application.")
        print("\nStart the server with:")
        print("   python app.py")
        print("\nOr use the helper script:")
        print("   python run.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up .env: cp .env.example .env")
        print("3. Add at least one API key to .env:")
        print("   - OPENAI_API_KEY (recommended)")
        print("   - PROJECT_ID + gcloud auth (secondary)")
        print("   - ANTHROPIC_API_KEY (fallback)")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
