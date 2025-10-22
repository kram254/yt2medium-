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
from ai_providers import AIProviderManager, get_youtube_transcript, detect_input_type, scrape_web_content, research_trending_topic

load_dotenv()

def generate_blog_post(ai_manager, user_input, enhance=False):
    input_type = detect_input_type(user_input)
    
    if input_type == 'youtube':
        print(f"🎥 Processing YouTube video: {user_input}")
    elif input_type == 'url':
        print(f"🔗 Processing URL: {user_input}")
    else:
        print(f"💭 Processing topic: {user_input}")
    
    print("🤖 Using AI providers: OpenAI (primary) → Gemini (secondary) → Anthropic (fallback)")
    print("⏳ Generating blog post...\n")
    
    if input_type == 'youtube':
        content_context = get_youtube_transcript(user_input)
    elif input_type == 'url':
        content_context = scrape_web_content(user_input)
    else:
        if any(keyword in user_input.lower() for keyword in ['trending', 'latest', 'today', 'recent', 'current']):
            content_context = research_trending_topic(user_input, ai_manager)
        else:
            content_context = f"User Request: {user_input}\n\nCreate comprehensive, well-researched content based on this topic or prompt."
    
    prompt = prompts.get_blog_gen_prompt()
    response = ai_manager.generate_content(prompt, content_context)
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
        description='AI Content to Medium - CLI Blog Post Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "https://www.youtube.com/watch?v=example"
  python cli.py "https://example.com/article" --enhance
  python cli.py "trending AI developments today" -o output.md
  python cli.py "create a post about quantum computing" --stats-only
        """
    )
    
    parser.add_argument(
        'input',
        help='YouTube URL, web URL, or topic/prompt'
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
    
    if not args.input or len(args.input.strip()) < 3:
        print("❌ Error: Input too short", file=sys.stderr)
        sys.exit(1)
    
    try:
        ai_manager = AIProviderManager()
        blog_text = generate_blog_post(ai_manager, args.input, args.enhance)
        
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
