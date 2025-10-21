import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    required_vars = ['PROJECT_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please create a .env file with these variables.")
        print("   You can copy .env.example and fill in your values:")
        print("   cp .env.example .env")
        sys.exit(1)
    
    print("✅ Environment variables configured")
    return True

def main():
    print("🎥 YouTube to Medium - AI Blog Post Generator")
    print("=" * 50)
    print()
    
    if check_environment():
        print(f"📍 Project ID: {os.getenv('PROJECT_ID')}")
        print(f"🌍 Location: {os.getenv('LOCATION', 'us-central1')}")
        print(f"🚀 Port: {os.getenv('PORT', '8080')}")
        print()
        print("Starting Flask server...")
        print("=" * 50)
        print()
        
        os.system('python app.py')

if __name__ == '__main__':
    main()
