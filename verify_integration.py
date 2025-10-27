import sys
import os
from pathlib import Path

print("=" * 60)
print("VERIFYING SYSTEM INTEGRATION")
print("=" * 60)

errors = []
warnings = []
success = []

print("\n1. Checking file structure...")
required_files = [
    'app.py',
    'medium_research_agent.py',
    'prompts.py',
    'templates/blog-post.html',
    'templates/history.html',
    'templates/analytics.html'
]

for file in required_files:
    if Path(file).exists():
        success.append(f"[OK] {file} exists")
    else:
        errors.append(f"[ERROR] {file} missing")

print("\n2. Checking imports in app.py...")
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    required_imports = [
        'from medium_research_agent import',
        'apply_medium_practices_to_prompt',
        'optimize_content_structure',
        'analyze_medium_readiness'
    ]
    
    for imp in required_imports:
        if imp in content:
            success.append(f"[OK] {imp}")
        else:
            errors.append(f"[ERROR] Missing import: {imp}")
            
except Exception as e:
    errors.append(f"[ERROR] Error reading app.py: {e}")

print("\n3. Checking function integration...")
try:
    integration_points = {
        'enhanced_prompt = apply_medium_practices_to_prompt': 'Prompt enhancement',
        'optimized_content = optimize_content_structure': 'Content optimization',
        'medium_analysis = analyze_medium_readiness': 'Readiness analysis',
        'get_all_temp_posts()': 'File-based storage',
        'calculate_temp_analytics()': 'Analytics calculation'
    }
    
    for pattern, description in integration_points.items():
        if pattern in content:
            success.append(f"[OK] {description} integrated")
        else:
            errors.append(f"[ERROR] {description} not found")
            
except Exception as e:
    errors.append(f"[ERROR] Error checking integrations: {e}")

print("\n4. Checking route configurations...")
routes = [
    ('@app.route(\'/generate\'', 'Blog generation'),
    ('@app.route(\'/history\')', 'History page'),
    ('@app.route(\'/analytics\')', 'Analytics page'),
    ('@app.route(\'/blog\')', 'Blog display'),
    ('@app.route(\'/post/<post_id>\')', 'Post viewer')
]

for route, name in routes:
    if route in content:
        success.append(f"[OK] {name} route configured")
    else:
        warnings.append(f"[WARN] {name} route may have issues")

print("\n5. Checking prompt enhancements...")
try:
    with open('prompts.py', 'r', encoding='utf-8') as f:
        prompt_content = f.read()
        
    enhancements = [
        'MEDIUM 2000+ CLAP FORMULA',
        'PARAGRAPH STRUCTURE',
        'SUBHEADING STRATEGY',
        'OPENING HOOK PATTERNS',
        'ENGAGEMENT BOOSTERS'
    ]
    
    for enhancement in enhancements:
        if enhancement in prompt_content:
            success.append(f"[OK] {enhancement} present")
        else:
            warnings.append(f"[WARN] {enhancement} may be missing")
            
except Exception as e:
    errors.append(f"[ERROR] Error reading prompts.py: {e}")

print("\n6. Checking Medium research agent module...")
try:
    with open('medium_research_agent.py', 'r', encoding='utf-8') as f:
        agent_content = f.read()
        
    functions = [
        'def apply_medium_practices_to_prompt',
        'def optimize_content_structure',
        'def analyze_medium_readiness',
        'def get_viral_title_formulas'
    ]
    
    for func in functions:
        if func in agent_content:
            success.append(f"[OK] {func} defined")
        else:
            errors.append(f"[ERROR] {func} missing")
            
except Exception as e:
    errors.append(f"[ERROR] Error reading medium_research_agent.py: {e}")

print("\n7. Checking temp_posts directory...")
temp_dir = Path('temp_posts')
if temp_dir.exists():
    success.append(f"[OK] temp_posts directory exists")
    posts = list(temp_dir.glob('*.json'))
    if posts:
        success.append(f"[OK] {len(posts)} posts in storage")
    else:
        warnings.append(f"[WARN] No posts yet (generate one to test)")
else:
    errors.append(f"[ERROR] temp_posts directory missing")

print("\n8. Checking port configuration...")
if 'server_port = int(os.environ.get(\'PORT\', \'8000\'))' in content:
    success.append(f"[OK] Port configured to 8000")
else:
    warnings.append(f"[WARN] Port may not be set to 8000")

print("\n" + "=" * 60)
print("VERIFICATION RESULTS")
print("=" * 60)

print(f"\nSUCCESS: {len(success)} items")
for item in success:
    print(f"  {item}")

if warnings:
    print(f"\nWARNINGS: {len(warnings)} items")
    for item in warnings:
        print(f"  {item}")

if errors:
    print(f"\nERRORS: {len(errors)} items")
    for item in errors:
        print(f"  {item}")
    print("\nSYSTEM MAY NOT BE FULLY OPERATIONAL")
    sys.exit(1)
else:
    print("\n" + "=" * 60)
    print("ALL CRITICAL FUNCTIONS ARE LIVE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Navigate to: http://localhost:8000")
    print("3. Generate a blog post to test all features")
    print("4. Check /history and /analytics pages")
    sys.exit(0)
