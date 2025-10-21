import os
import sys
import csv
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import prompts
from util import (
    extract_title_from_markdown,
    validate_youtube_url,
    clean_markdown,
    estimate_reading_time,
    calculate_engagement_score
)
from ai_providers import AIProviderManager, get_youtube_transcript

load_dotenv()

def generate_blog_post(ai_manager, youtube_url):
    video_context = get_youtube_transcript(youtube_url)
    prompt = prompts.get_blog_gen_prompt()
    response = ai_manager.generate_content(prompt, video_context)
    return clean_markdown(response)

def process_batch(input_file, output_dir='output'):
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        if input_file.endswith('.csv'):
            reader = csv.DictReader(f)
            urls = [row['url'] for row in reader if 'url' in row]
        elif input_file.endswith('.json'):
            data = json.load(f)
            urls = data if isinstance(data, list) else data.get('urls', [])
        else:
            urls = [line.strip() for line in f if line.strip()]
    
    ai_manager = AIProviderManager()
    total = len(urls)
    
    print(f"🎥 Processing {total} videos...")
    print(f"📁 Output directory: {output_path}")
    print("🤖 Using AI providers: OpenAI (primary) → Gemini (secondary) → Anthropic (fallback)")
    print("=" * 60)
    
    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{total}] Processing: {url}")
        
        if not validate_youtube_url(url):
            print(f"   ❌ Invalid URL, skipping")
            results.append({
                'url': url,
                'status': 'failed',
                'error': 'Invalid URL'
            })
            continue
        
        try:
            blog_text = generate_blog_post(ai_manager, url)
            title = extract_title_from_markdown(blog_text)
            
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
            safe_title = safe_title[:100]
            
            filename = f"{timestamp}_{idx:03d}_{safe_title}.md"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(blog_text)
            
            word_count = len(blog_text.split())
            reading_time = estimate_reading_time(blog_text)
            engagement_score = calculate_engagement_score(blog_text)
            
            print(f"   ✅ Generated: {filename}")
            print(f"   📊 Words: {word_count} | Time: {reading_time} | Score: {engagement_score}/100")
            
            results.append({
                'url': url,
                'status': 'success',
                'filename': filename,
                'title': title,
                'word_count': word_count,
                'engagement_score': engagement_score
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'url': url,
                'status': 'failed',
                'error': str(e)
            })
    
    report_file = output_path / f"batch_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    fail_count = total - success_count
    
    print("\n" + "=" * 60)
    print("📊 BATCH PROCESSING COMPLETE")
    print("=" * 60)
    print(f"✅ Successful: {success_count}/{total}")
    print(f"❌ Failed: {fail_count}/{total}")
    print(f"📄 Report saved: {report_file}")
    print("=" * 60)

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_process.py <input_file> [output_dir]")
        print("\nInput file formats supported:")
        print("  - Text file (.txt): One URL per line")
        print("  - CSV file (.csv): Must have 'url' column")
        print("  - JSON file (.json): Array of URLs or {urls: [...]}")
        print("\nExamples:")
        print("  python batch_process.py urls.txt")
        print("  python batch_process.py urls.csv output_blogs")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'output'
    
    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)
    
    process_batch(input_file, output_dir)

if __name__ == '__main__':
    main()
