import sys
import os
import argparse
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

def generate_blog_post(ai_manager, youtube_url, enhance=False):
    print(f"🎥 Processing video: {youtube_url}")
    print("🤖 Using AI providers: OpenAI (primary) → Gemini (secondary) → Anthropic (fallback)")
    print("⏳ Generating blog post...\n")
    
    video_context = get_youtube_transcript(youtube_url)
    prompt = prompts.get_blog_gen_prompt()
    response = ai_manager.generate_content(prompt, video_context)
    blog_text = clean_markdown(response)
    
    if enhance:
        print("✨ Applying enhancement...\n")
        enhancement_prompt = f"""
Enhance this Medium blog post to make it even more engaging and viral-worthy.

Original post:
{blog_text}

Return the enhanced version in Markdown format.
"""
        blog_text = clean_markdown(ai_manager.generate_content(enhancement_prompt))
    
    return blog_text

def print_stats(blog_text):
    title = extract_title_from_markdown(blog_text)
    reading_time = estimate_reading_time(blog_text)
    word_count = len(blog_text.split())
    engagement_score = calculate_engagement_score(blog_text)
    
    print("=" * 60)
    print("📊 BLOG POST STATISTICS")
    print("=" * 60)
    print(f"📝 Title: {title}")
    print(f"📖 Reading Time: {reading_time}")
    print(f"🔤 Word Count: {word_count} words")
    print(f"⭐ Engagement Score: {engagement_score}/100")
    print("=" * 60)

def save_to_file(content, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(
        description='YouTube to Medium - CLI Blog Post Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "https://www.youtube.com/watch?v=example"
  python cli.py "https://youtu.be/example" --enhance
  python cli.py "https://www.youtube.com/watch?v=example" -o output.md
  python cli.py "https://www.youtube.com/watch?v=example" --stats-only
        """
    )
    
    parser.add_argument(
        'url',
        help='YouTube video URL'
    )
    
    
    parser.add_argument(
        '-e', '--enhance',
        action='store_true',
        help='Apply advanced enhancement pass'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: print to stdout)'
    )
    
    parser.add_argument(
        '-s', '--stats-only',
        action='store_true',
        help='Show only statistics without full content'
    )
    
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Skip statistics display'
    )
    
    args = parser.parse_args()
    
    if not validate_youtube_url(args.url):
        print("❌ Error: Invalid YouTube URL", file=sys.stderr)
        sys.exit(1)
    
    try:
        ai_manager = AIProviderManager()
        blog_text = generate_blog_post(ai_manager, args.url, args.enhance)
        
        if not args.no_stats:
            print_stats(blog_text)
            print()
        
        if args.stats_only:
            sys.exit(0)
        
        if args.output:
            save_to_file(blog_text, args.output)
        else:
            print("=" * 60)
            print("📄 GENERATED BLOG POST")
            print("=" * 60)
            print()
            print(blog_text)
            print()
        
        print("✅ Blog post generation complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
