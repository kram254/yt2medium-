from flask import Flask, render_template, request, redirect, url_for, jsonify, session, g
import os
import re
import markdown
from dotenv import load_dotenv
from datetime import datetime
import prompts
from util import (
    extract_title_from_markdown,
    estimate_reading_time,
    extract_key_quotes,
    validate_youtube_url,
    clean_markdown,
    calculate_engagement_score,
    extract_video_id,
    extract_urls,
    remove_urls_from_text
)
from seo_analyzer import analyze_seo, generate_seo_recommendations
from ai_providers import AIProviderManager, get_youtube_transcript, detect_input_type, scrape_web_content, research_trending_topic
from prompts import get_blog_gen_prompt, get_image_gen_prompt
from export_handler import export_to_medium, export_to_linkedin, create_twitter_thread, export_to_devto, export_to_hashnode, export_to_ghost, export_to_wordpress, export_to_json, export_to_txt, export_to_notion, export_to_email_html, get_export_formats
from content_library import save_post, get_post, get_all_posts, search_posts, get_stats, add_to_batch_queue, get_batch_queue, update_batch_status, save_draft, get_draft, get_all_drafts, delete_draft, save_post_version, get_post_versions, get_post_version, schedule_post, get_scheduled_posts, update_scheduled_post_status, delete_scheduled_post
from cache_manager import get_cache_manager
from rate_limiter import get_rate_limiter
from job_queue import get_job_queue
from advanced_analytics import analyze_readability, analyze_keywords, analyze_sentence_structure, analyze_tone_sentiment, analyze_engagement_potential, calculate_viral_potential, generate_content_insights, generate_improvement_suggestions
from file_processor import process_uploaded_file
from werkzeug.utils import secure_filename
from content_templates import TEMPLATES, TONE_PRESETS, get_template_prompt
from ai_editor import get_section_rewrite_prompt, get_tone_adjustment_prompt, get_expand_prompt, get_compress_prompt, get_title_alternatives_prompt, get_meta_description_prompt
from medium_research_agent import apply_medium_practices_to_prompt, optimize_content_structure, analyze_medium_readiness
from linkedin_agent import generate_linkedin_post
from github_handler import get_github_handler
from social_auth import get_medium_auth, get_linkedin_auth
from social_storage import get_social_account_manager
from supabase_client import get_supabase_manager
from post_scheduler import get_scheduler
from progress_tracker import get_progress_tracker
from diagram_generator import get_diagram_generator
import time
import random
import json
import uuid
import tempfile
from pathlib import Path
from functools import wraps
from datetime import timedelta
import hashlib
import hmac

print("=" * 60)
print("STARTING FLASK APP")
print("=" * 60)

TEMP_STORAGE_DIR = Path(__file__).parent / 'temp_posts'
TEMP_STORAGE_DIR.mkdir(exist_ok=True)
print(f"Temp storage directory: {TEMP_STORAGE_DIR}")
print(f"Temp storage exists: {TEMP_STORAGE_DIR.exists()}")

def cleanup_old_temp_files():
    try:
        import time
        current_time = time.time()
        for temp_file in TEMP_STORAGE_DIR.glob('*.json'):
            if current_time - temp_file.stat().st_mtime > 86400:
                temp_file.unlink()
    except Exception as e:
        print(f"Warning: Failed to cleanup temp files: {e}")

cleanup_old_temp_files()

def get_all_temp_posts():
    posts = []
    try:
        for temp_file in sorted(TEMP_STORAGE_DIR.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    post_data = json.load(f)
                    post_data['id'] = temp_file.stem
                    post_data['created_at'] = datetime.fromtimestamp(temp_file.stat().st_mtime).isoformat()
                    posts.append(post_data)
            except Exception as e:
                print(f"Error reading {temp_file}: {e}")
    except Exception as e:
        print(f"Error listing temp posts: {e}")
    return posts

def calculate_temp_analytics():
    posts = get_all_temp_posts()
    
    total_posts = len(posts)
    total_words = sum(p.get('word_count', 0) for p in posts)
    avg_engagement = sum(p.get('engagement_score', 0) for p in posts) / total_posts if total_posts > 0 else 0
    avg_seo = sum(p.get('seo_score', 0) for p in posts) / total_posts if total_posts > 0 else 0
    avg_viral = sum(p.get('viral_potential', 0) for p in posts) / total_posts if total_posts > 0 else 0
    
    return {
        'total_posts': total_posts,
        'total_words_written': total_words,
        'avg_engagement_score': round(avg_engagement),
        'avg_seo_score': round(avg_seo),
        'avg_viral_potential': round(avg_viral),
        'recent_posts': posts[:5] if posts else []
    }

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https' if os.environ.get('FLASK_ENV') == 'production' else 'http'

print(f"Flask app name: {app.name}")
print(f"Flask root path: {app.root_path}")
print(f"Template folder: {app.template_folder}")

ai_manager = None

DEFAULT_MODEL = 'gpt-4o'

BANNED_PROMPT_PHRASES = [
    "Let's dive into",
    "In today's fast-paced world",
    "In the ever-evolving landscape",
    "In conclusion",
    "Overall",
    "Hope this helps",
    "cutting-edge",
    "unlock the power of",
    "game-changing",
    "seamless experience",
    "I think",
    "I believe",
    "maybe",
    "could potentially",
    "revolutionary",
    "disruptive",
    "seamless",
    "leverage",
    "robust",
    "delve into",
    "great question",
    "solutions",
    "ecosystem",
    "best-in-class",
    "next-generation",
    "enterprise-grade",
    "world-class",
    "might potentially",
    "could possibly",
    "seems to perhaps",
    "may be able to"
]

def _remove_banned_phrases(text):
    if not isinstance(text, str) or not text:
        return text
    result = text
    for phrase in BANNED_PROMPT_PHRASES:
        result = re.sub(re.escape(phrase), '', result, flags=re.IGNORECASE)
    result = re.sub(r'\s{2,}', ' ', result).strip()
    return result

def _sanitize_prompt_value(value):
    if isinstance(value, dict):
        return {k: _sanitize_prompt_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_prompt_value(v) for v in value]
    if isinstance(value, str):
        v = re.sub(r'https?://\S+', '', value)
        v = _remove_banned_phrases(v)
        return v
    return value

def require_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = session.get('access_token')
        if not access_token:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login', next=request.url))

        supabase = get_supabase_manager()
        if not supabase:
            if request.is_json:
                return jsonify({'error': 'Database not configured'}), 503
            return redirect(url_for('login'))

        user_response = supabase.get_user(access_token)

        if not user_response or not user_response.user:
            # Try refreshing the token before giving up
            refresh_token = session.get('refresh_token')
            if refresh_token:
                new_session = supabase.refresh_session(refresh_token)
                if new_session and hasattr(new_session, 'session') and new_session.session:
                    session['access_token'] = new_session.session.access_token
                    session['refresh_token'] = new_session.session.refresh_token
                    session['user_id'] = new_session.user.id
                    session['user_email'] = new_session.user.email
                    g.user = new_session.user
                    g.user_id = new_session.user.id
                    return f(*args, **kwargs)

            session.clear()
            if request.is_json:
                return jsonify({'error': 'Session expired'}), 401
            return redirect(url_for('login'))

        g.user = user_response.user
        g.user_id = user_response.user.id
        # Keep session user_id in sync
        session['user_id'] = user_response.user.id
        return f(*args, **kwargs)
    return decorated_function

# ── Authentication Routes ───────────────────────────────────────────

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('signup.html', error="Email and password required")
            
        supabase = get_supabase_manager()
        res = supabase.sign_up(email, password)
        
        if res and res.user:
            return render_template('login.html', message="Check your email for a confirmation link!")
        else:
            return render_template('signup.html', error="Signup failed. Account might already exist.")
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        supabase = get_supabase_manager()
        res = supabase.sign_in(email, password)
        
        if res and res.session:
            session.permanent = True
            session['access_token'] = res.session.access_token
            session['refresh_token'] = res.session.refresh_token
            session['user_id'] = res.user.id
            session['user_email'] = res.user.email
            
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        else:
            return render_template('login.html', error="Invalid email or password")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    supabase = get_supabase_manager()
    supabase.sign_out()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        supabase = get_supabase_manager()
        supabase.reset_password(email)
        return render_template('forgot-password.html', message="If an account exists, a reset link has been sent.")
    return render_template('forgot-password.html')

@app.route('/auth/google')
def auth_google():
    """Initiate Google OAuth via Supabase."""
    supabase = get_supabase_manager()
    if not supabase:
        return redirect(url_for('login'))
    callback_url = url_for('auth_callback', _external=True)
    result = supabase.sign_in_with_google(redirect_url=callback_url)
    if result and hasattr(result, 'url') and result.url:
        return redirect(result.url)
    return redirect(url_for('login'))

@app.route('/auth/callback')
def auth_callback():
    """Handle Supabase Auth redirects (OAuth & email confirmation)."""
    code = request.args.get('code')
    if code:
        supabase = get_supabase_manager()
        if supabase:
            result = supabase.exchange_code_for_session(code)
            if result and hasattr(result, 'session') and result.session:
                session.permanent = True
                session['access_token'] = result.session.access_token
                session['refresh_token'] = result.session.refresh_token
                session['user_id'] = result.user.id
                session['user_email'] = result.user.email
                return redirect(url_for('index'))
    return redirect(url_for('login'))

# ── Main Routes ─────────────────────────────────────────────────────

@app.route('/')
@require_session
def index():
    return render_template('index.html', user=g.user)

def validate_request_signature(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            signature = request.headers.get('X-Request-Signature')
            if not signature:
                return jsonify({'error': 'Missing request signature'}), 401
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_check(max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id', request.remote_addr or 'anonymous')
            endpoint = request.endpoint or 'unknown'
            
            rate_limiter = get_rate_limiter()
            allowed, retry_after, count = rate_limiter.check_rate_limit(
                user_id, endpoint, max_requests, window
            )
            
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': retry_after,
                    'requests': count
                }), 429
            
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                resp, status = response[0], response[1] if len(response) > 1 else 200
                if isinstance(resp, dict) or hasattr(resp, 'json'):
                    return response
            return response
        return decorated_function
    return decorator

def get_ai_manager():
    global ai_manager
    if ai_manager is None:
        print("Initializing AIProviderManager...")
        ai_manager = AIProviderManager()
        print("AIProviderManager initialized successfully")
        
        has_provider = False
        if ai_manager.openai_client:
            print("✓ OpenAI configured")
            has_provider = True
        if ai_manager.gemini_client:
            print("✓ Gemini configured")
            has_provider = True
        if ai_manager.anthropic_client:
            print("✓ Anthropic configured")
            has_provider = True
        if ai_manager.openrouter_api_key:
            print("✓ OpenRouter configured")
            has_provider = True
        
        if not has_provider:
            print("⚠ WARNING: No AI providers configured! Add API keys to .env file")
    
    return ai_manager


def generate_images_for_blog(blog_title, blog_content):
    try:
        print(f"[IMAGE GEN] Starting image generation for: {blog_title[:50]}")
        prompt1 = prompts.get_image_gen_prompt(blog_title)
        print(f"[IMAGE GEN] Prompt 1 length: {len(prompt1)} chars")
        prompt2 = prompts.get_content_image_prompt(blog_title, blog_content)
        print(f"[IMAGE GEN] Prompt 2 length: {len(prompt2)} chars")
        images = get_ai_manager().generate_images(prompt1, prompt2)
        print(f"[IMAGE GEN] Returned images: {[type(img).__name__ if img else 'None' for img in images]}")
        if images[0]:
            print(f"[IMAGE GEN] Image 1 size: {len(str(images[0]))} chars")
        if images[1]:
            print(f"[IMAGE GEN] Image 2 size: {len(str(images[1]))} chars")
        return images
    except Exception as e:
        print(f"[IMAGE GEN] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return [None, None]

def generate_blog_post_text(user_input, model, template=None, tone=None, industry=None):
    """
    Generate blog post from user input which may contain:
    - Multiple URLs (articles, YouTube videos, GitHub repos)
    - Plain text/transcript
    - Or a mix of all three
    
    This function extracts and combines content from ALL sources to create a comprehensive context.
    """
    try:
        # Extract all URLs from the input (supports multiple URLs in one input)
        urls = extract_urls(user_input)
        print(f"[INPUT] Found {len(urls)} URLs in input")
        
        # Extract any text that isn't a URL (e.g., user commentary, transcript)
        additional_text = remove_urls_from_text(user_input).strip()
        if additional_text:
            print(f"[INPUT] Found {len(additional_text)} chars of additional text")
        
        # Collect content from all sources into one combined context
        # This allows blog posts about multiple related sources (e.g., article + video)
        content_parts = []
        has_youtube_content = False  # Track if we have YouTube content for enhancement later
        
        # Process each URL individually (article, YouTube, GitHub, etc.)
        for url in urls:
            print(f"[INPUT] Processing URL: {url[:80]}...")
            url_type = detect_input_type(url)
            print(f"[INPUT] URL type: {url_type}")
            
            # Handle YouTube videos - extract full transcript
            if url_type == 'youtube':
                try:
                    yt_content = get_youtube_transcript(url)
                    content_parts.append(f"=== YOUTUBE VIDEO CONTENT ===\n{yt_content}")
                    has_youtube_content = True  # Mark that we have YouTube content
                    print(f"[INPUT] YouTube content extracted: {len(yt_content)} chars")
                except Exception as yt_error:
                    print(f"[INPUT] YouTube extraction failed: {yt_error}")
                    try:
                        from ai_providers import _get_youtube_fallback
                        fallback = _get_youtube_fallback(url)
                        if fallback:
                            content_parts.append(f"=== YOUTUBE VIDEO (METADATA) ===\n{fallback}")
                            print(f"[INPUT] YouTube metadata extracted")
                    except:
                        content_parts.append(f"=== YOUTUBE VIDEO ===\nURL: {url}\nNote: Transcript unavailable")
            
            # Handle GitHub repositories - extract README
            elif url_type == 'github':
                try:
                    github = get_github_handler()
                    readme = github.get_readme(url)
                    if readme:
                        content_parts.append(f"=== GITHUB REPOSITORY ===\n{readme}")
                        print(f"[INPUT] GitHub content extracted: {len(readme)} chars")
                except Exception as gh_error:
                    print(f"[INPUT] GitHub extraction failed: {gh_error}")
                    content_parts.append(f"=== GITHUB REPOSITORY ===\nURL: {url}")
            
            # Handle regular web URLs - scrape article content
            elif url_type == 'url':
                try:
                    web_content = scrape_web_content(url)
                    content_parts.append(f"=== WEB ARTICLE ===\n{web_content}")
                    print(f"[INPUT] Web content extracted: {len(web_content)} chars")
                except Exception as url_error:
                    print(f"[INPUT] Web scraping failed: {url_error}")
                    content_parts.append(f"=== WEB ARTICLE ===\nURL: {url}\nNote: Unable to scrape content")
        
        # Add any additional text provided by the user (commentary, transcript, notes)
        if additional_text and len(additional_text) > 10:
            content_parts.append(f"=== USER PROVIDED CONTEXT ===\n{additional_text}")
        
        # If no URLs were found, treat entire input as topic/text request
        if not content_parts:
            print(f"[INPUT] No URLs found, treating as topic")
            if any(keyword in user_input.lower() for keyword in ['trending', 'latest', 'today', 'recent', 'current']):
                content_context = research_trending_topic(user_input, get_ai_manager())
            else:
                content_context = f"User Request: {user_input}\n\nCreate comprehensive, well-researched content based on this topic or prompt."
        else:
            # Combine all content sources into one unified context
            # This allows blog posts about multiple related sources (e.g., article + video)
            content_context = "\n\n".join(content_parts)
            print(f"[INPUT] Combined content from {len(content_parts)} sources")
        
        print(f"[INPUT] Total content context: {len(content_context)} chars")
        
        # Apply content length limits to avoid token limit issues
        max_content_chars = 80000
        if len(content_context) > max_content_chars:
            first_part_size = int(max_content_chars * 0.6)
            last_part_size = int(max_content_chars * 0.3)
            first_part = content_context[:first_part_size]
            last_part = content_context[-last_part_size:]
            truncation_notice = f"\n\n[Content truncated: Original {len(content_context)} chars, showing {first_part_size + last_part_size} chars]\n\n"
            content_context = first_part + truncation_notice + last_part
            print(f"Content truncated to: {len(content_context)} chars")
        
        base_prompt = prompts.get_blog_gen_prompt()
        
        if template:
            template_addition = get_template_prompt(template, tone, industry)
            prompt = base_prompt + "\n\n" + template_addition
        else:
            prompt = base_prompt
        
        topic_for_optimization = user_input[:100]
        enhanced_prompt = apply_medium_practices_to_prompt(prompt, topic_for_optimization)
        
        print(f"Calling AI manager with model: {model}")
        response = get_ai_manager().generate_content(enhanced_prompt, content_context, model)
        print(f"AI response length: {len(response) if response else 0}")
        
        cleaned_content = clean_markdown(response)
        optimized_content = optimize_content_structure(cleaned_content)
        print(f"Final optimized content length: {len(optimized_content) if optimized_content else 0}")
        
        # Apply transcript enhancement if we have YouTube content
        if has_youtube_content and content_context and len(content_context) > 100:
            print("Enhancing blog post with YouTube transcript...")
            optimized_content = enhance_blog_with_transcript(optimized_content, content_context)
            print(f"Transcript-enhanced content length: {len(optimized_content) if optimized_content else 0}")
        
        return optimized_content
    except Exception as e:
        print(f"Exception in generate_blog_post_text: {str(e)}")
        raise Exception(f"Failed to generate blog post: {str(e)}")

def enhance_blog_with_transcript(blog_text, transcript):
    try:
        enhancement_prompt = f"""
You are an expert editor specializing in transforming blog posts using video transcript insights.

🚨 CRITICAL: The blog post and transcript MUST be about the SAME topic. Do not change the topic. Stay focused.

Your task: Enhance the wording, depth, and accuracy of this Medium blog post using the YouTube video transcript.

ENHANCEMENT INSTRUCTIONS:
1. VERIFY the blog post is about the same topic as the transcript - if not, rewrite to match the transcript
2. Use specific quotes, examples, and details from the transcript to enrich the content
3. Replace generic statements with precise information from the video
4. Add concrete examples and real-world scenarios mentioned in the transcript
5. Incorporate exact statistics, numbers, and data points from the video
6. Use the speaker's authentic voice and terminology where appropriate
7. Expand sections with additional context from the transcript
8. Ensure all claims are backed by transcript content
9. Maintain the blog structure while deepening the content
10. Target 1200-1800 words using transcript details
11. Keep the writing style natural and engaging
12. DO NOT deviate from the transcript topic - this is mandatory

YouTube Transcript:
{transcript[:8000]}

Blog Post to Enhance:
{blog_text}

Return the enhanced blog post in Markdown format. No explanations or meta-commentary.
"""
        response = get_ai_manager().generate_content(enhancement_prompt)
        return response if response else blog_text
    except Exception as e:
        print(f"Transcript enhancement error: {e}")
        return blog_text

def enhance_blog_post(blog_text):
    try:
        enhancement_prompt = f"""
You are an expert editor and writing coach. Enhance this Medium blog post to make it sound like it was written by a confident, clear, and direct human - not an AI.

Apply these rules meticulously:

HUMAN WRITING STYLE:
- Write like humans speak. No corporate jargon or marketing fluff.
- Be confident and direct. Remove softening phrases like "I think," "I believe," "maybe," or "could."
- Use active voice over passive voice.
- Use "you" more than "we" when addressing readers.
- Use contractions like "I'll," "won't," and "can't" for a warmer tone.

BANNED WORDS - REMOVE OR REPLACE:
- Softening Hedges: "a bit," "a little," "just," "pretty," "quite," "rather," "really," "very," "arguably," "it seems," "sort of," "kind of"
- Corporate Jargon: "agile," "assistance" (use "help"), "best practices" (use "proven approaches"), "blazing fast" (use metrics), "delve" (use "go into"), "disrupt," "facilitate" (use "help"), "game-changing," "innovative," "leverage" (use "use"), "robust" (use "strong"), "seamless" (use "automatic"), "utilize" (use "use")
- AI Patterns: Never use "Let's dive into," "In today's fast-paced world," "In the ever-evolving landscape." Never end with "In conclusion," "Overall," "Hope this helps!"

ENHANCEMENT FOCUS:
1. Make the opening more compelling and hook readers immediately
2. Add emotional hooks and relatable scenarios
3. Improve flow and transitions between sections
4. Strengthen the conclusion with clear action steps
5. Replace vague language with specific facts and data
6. Make content concrete, visual, and falsifiable
7. Use realistic examples (no foo/bar/baz placeholders)
8. Add code snippets, workflows, or visual explanations where helpful
9. EXPAND content - do NOT compress or shorten
10. If the post is under 1000 words, add more examples, case studies, and detailed explanations
11. Target 1200-1800 words for comprehensive depth

Original post:
{blog_text}

Return the enhanced version in Markdown format. No explanations or meta-commentary.
"""
        response = get_ai_manager().generate_content(enhancement_prompt)
        return response if response else blog_text
    except Exception as e:
        print(f"Enhancement error: {e}")
        return blog_text

@app.route('/api/generate-with-content', methods=['POST'])
@require_session
def generate_with_content():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        model = data.get('model', DEFAULT_MODEL)
        template = data.get('template')
        tone = data.get('tone')
        industry = data.get('industry')
        
        if not title or not content:
            return jsonify({'error': 'Title and content required'}), 400
        
        if len(title) > 500:
            return jsonify({'error': 'Title too long'}), 400
        
        if len(content) < 100:
            return jsonify({'error': 'Content too short'}), 400
        
        full_context = f"Title: {title}\n\nContent:\n{content}"
        
        blog_post_text = generate_blog_post_text(
            full_context,
            model,
            template=template,
            tone=tone,
            industry=industry
        )
        
        if not blog_post_text:
            return jsonify({'error': 'Failed to generate blog post'}), 500
        
        return jsonify({
            'success': True,
            'blog_post': blog_post_text,
            'redirect': f'/blog?post_id={session.get("current_post_id", "")}'
        })
    except Exception as e:
        print(f"Generate with content error: {e}")
        return jsonify({'error': 'Generation failed'}), 500

@app.route('/api/surprise-me', methods=['POST'])
@require_session
def surprise_me():
    try:
        start_time = time.time()
        data = request.get_json() or {}
        user_preferences = data.get('user_preferences') or {}
        topics_of_interest = user_preferences.get('topics_of_interest') or []
        excluded_topics = user_preferences.get('excluded_topics') or []
        current_date = datetime.now().strftime("%B %d, %Y")
        cache = get_cache_manager()
        cached_cards = cache.get('surprise_me_v2')
        cards_payload = cached_cards if isinstance(cached_cards, list) else None
        if not cards_payload:
            ai_prompt = (
                f"You are an expert AI/ML content strategist and trend researcher. Today is {current_date}.\n"
                "Your job: identify the TOP 3 most trending, newsworthy, developer-relevant topics in AI, ML, LLMs, "
                "and open-source tooling right now (not only Python) — as if you had access to X/Twitter trends, YouTube trending, "
                "Medium articles, GitHub trending, Hacker News front page, and Reddit r/MachineLearning.\n"
                "The information MUST be verifiable and legit. Do not hallucinate trends.\n"
                "For each topic, generate a complete, ready-to-use Medium blog post prompt.\n\n"
                "Return ONLY a raw JSON object with no markdown fences, no prose, no explanation.\n"
                'The JSON must have exactly this structure:\n'
                '{"cards": [\n'
                '  {"rank": 1, "rank_badge": "#1 Trending", "headline": "punchy 6-10 word title", '
                '"subtext": "one sentence hook", "why_now": "what makes this timely", '
                '"platforms": ["x_twitter", "youtube"], "composite_score": 88, '
                '"estimated_read_time": "9 min read", "keywords": ["kw1", "kw2"], '
                '"chat_input_prompt": "Write a complete publish-ready Medium blog post titled [SPECIFIC TITLE]. '
                'Angle: [SPECIFIC ANGLE]. The article must cover: (1) Hook with bold technical claim, '
                '(2) Background and why this matters now, (3) Technical deep dive with Python code example, '
                '(4) Real-world use cases, (5) Critical perspective with limitations, '
                '(6) Actionable takeaways for this week. Tone: technical but accessible, first-person, no fluff. '
                'Target reader: senior developer or ML engineer. Length: 1800-2400 words. '
                'Medium tags: [TAG1, TAG2, TAG3, TAG4, TAG5]. End with a strong CTA."},'
                '  {"rank": 2, "rank_badge": "#2 Trending", ...same shape...},'
                '  {"rank": 3, "rank_badge": "#3 Trending", ...same shape...}'
                ']}\n\n'
                "Rules:\n"
                "- All 3 topics must be DIFFERENT with no overlap.\n"
                "- composite_score must be a number 60-100.\n"
                "- chat_input_prompt must be at least 350 characters, name the specific tool/paper/model, "
                "include the angle, full outline, tone, length target, and Medium tags.\n"
                "- platforms array values must be from: x_twitter, youtube, instagram, reddit, medium only.\n"
                f"- Focus on releases or trends from the past 7 days as of {current_date}.\n"
            )
            if topics_of_interest:
                ai_prompt += "User interests (bias selection toward these): " + ", ".join(str(x) for x in topics_of_interest) + "\n"
            if excluded_topics:
                ai_prompt += "Excluded topics (do NOT suggest): " + ", ".join(str(x) for x in excluded_topics) + "\n"
            ai_result = get_ai_manager().generate_content(ai_prompt)
            parsed = None
            try:
                parsed = json.loads(ai_result)
            except Exception:
                if isinstance(ai_result, str):
                    first = ai_result.find("{")
                    last = ai_result.rfind("}")
                    if first != -1 and last != -1 and last > first:
                        snippet = ai_result[first : last + 1]
                        try:
                            parsed = json.loads(snippet)
                        except Exception:
                            parsed = None
            if isinstance(parsed, dict) and isinstance(parsed.get('cards'), list) and len(parsed['cards']) >= 1:
                cards_payload = parsed['cards']
                cache.set('surprise_me_v2', cards_payload, ttl=300)
        evergreen_cards = [
            {
                "rank": 1,
                "rank_badge": "#1 Trending",
                "headline": "The Open-Source AI Agent Stacks Every Developer Should Know",
                "subtext": "Stop paying for wrappers — here are the agent frameworks quietly replacing closed platforms.",
                "why_now": "LangGraph, CrewAI, AutoGen, and Agno are all fighting for the top spot in production Python stacks right now.",
                "platforms": ["x_twitter", "youtube", "instagram"],
                "composite_score": 88,
                "estimated_read_time": "9 min read",
                "keywords": ["open source ai agents", "python agents", "llm orchestration"],
                "chat_input_prompt": "Write a complete, publish-ready Medium blog post titled 'The Open-Source AI Agent Stacks Every Developer Should Know in 2025'. Angle: A senior Python developer cutting through the noise to rank the top open-source agent frameworks by real production utility, not hype. The article must cover: (1) Hook -- open with a bold claim about why most developers are overpaying for closed AI wrappers, (2) What an agent stack actually is and why the architecture choice matters, (3) A side-by-side breakdown of LangGraph, CrewAI, AutoGen, and Agno -- their strengths, weaknesses, and ideal use cases, (4) A concrete Python code example showing how to build a simple research agent in the top-ranked framework, (5) Production considerations -- latency, cost, observability, and reliability tradeoffs, (6) Critical perspective -- when you should just use an API instead of a full agent framework, (7) Actionable takeaways: 5 things to benchmark before committing to a stack. Tone: technical but accessible, first-person, direct, no corporate jargon. Target reader: senior developer or ML engineer. Length: 2000-2400 words. Medium tags: Artificial Intelligence, Python, LLM, Open Source, Machine Learning. End with a CTA inviting readers to share their production stack."
            },
            {
                "rank": 2,
                "rank_badge": "#2 Trending",
                "headline": "Stop Shipping Blind: LLM Evaluation Tools for Python Teams",
                "subtext": "Your model is in production and you have no idea if it's degrading — here's how to fix that.",
                "why_now": "A wave of open-source LLM eval tooling just dropped as teams discover prompt regressions are invisible without proper evals.",
                "platforms": ["x_twitter", "youtube"],
                "composite_score": 82,
                "estimated_read_time": "8 min read",
                "keywords": ["llm evaluation", "prompt testing", "ai monitoring"],
                "chat_input_prompt": "Write a complete, publish-ready Medium blog post titled 'Stop Shipping Blind: The Modern LLM Evaluation Stack for Python Teams'. Angle: A battle-hardened ML engineer explaining why evals are the most underrated practice in AI engineering and showing exactly how to set them up in a real Python project. The article must cover: (1) Hook -- open with a scenario where a silent prompt regression caused a production incident nobody caught for three days, (2) Why traditional software testing completely fails for LLM applications, (3) A breakdown of the three categories of evals: functional correctness, quality scoring, and regression detection, (4) A hands-on Python code example using an open-source eval framework such as RAGAS, DeepEval, or LangSmith to set up a basic eval pipeline, (5) How to wire evals into a CI/CD pipeline so they run on every prompt change, (6) Critical perspective -- the limits of automated evals and when you still need human review, (7) Actionable setup checklist: what to instrument in your LLM app this week. Tone: direct, technical, first-person, written like a practitioner. Target reader: ML engineer or backend developer deploying LLM features. Length: 1900-2300 words. Medium tags: Machine Learning, Python, LLMOps, Production AI, Software Engineering. End with a CTA asking readers what their eval stack looks like."
            },
            {
                "rank": 3,
                "rank_badge": "#3 Trending",
                "headline": "Structured Outputs in Python: Making LLMs Behave Like Real APIs",
                "subtext": "Parsing LLM responses with string splits is a production disaster -- here's the grown-up solution.",
                "why_now": "OpenAI native structured output mode plus Pydantic v2 and Instructor has made reliable JSON from LLMs achievable and teams are migrating fast.",
                "platforms": ["x_twitter", "instagram"],
                "composite_score": 77,
                "estimated_read_time": "7 min read",
                "keywords": ["structured outputs", "pydantic", "llm json"],
                "chat_input_prompt": "Write a complete, publish-ready Medium blog post titled 'Structured Outputs in Python: Making LLMs Behave Like Real APIs'. Angle: A Python developer explaining how to eliminate fragile string parsing from LLM pipelines using structured output libraries with real, runnable code. The article must cover: (1) Hook -- open with the universal developer pain of shipping a prompt to production and watching it return malformed JSON at 2am, (2) The three eras of LLM output parsing: regex hacks, prompt-engineering JSON, and native structured outputs, (3) A deep dive into the Instructor library and how it wraps OpenAI, Anthropic, and Gemini with Pydantic validation, (4) Two complete Python code examples showing the old fragile approach versus the structured output approach, (5) How to handle validation errors, retries, and partial outputs gracefully, (6) Performance and cost implications -- does structured mode actually cost more tokens, (7) When to use JSON mode versus function calling versus native structured outputs. Tone: technical, practical, first-person, no hand-waving. Target reader: Python developer building LLM-powered features. Length: 1800-2200 words. Medium tags: Python, AI, LLM, Pydantic, Software Engineering. End with a CTA encouraging readers to refactor one fragile parser this week."
            }
        ]
        raw_cards = cards_payload if isinstance(cards_payload, list) and len(cards_payload) >= 1 else None
        valid_platforms = {"x_twitter", "youtube", "instagram"}
        def sanitize_card(card, fallback):
            if not isinstance(card, dict):
                return dict(fallback)
            out = {}
            out['rank'] = int(card.get('rank') or fallback['rank'])
            out['rank_badge'] = str(card.get('rank_badge') or fallback['rank_badge'])
            out['headline'] = str(card.get('headline') or fallback['headline'])[:200]
            out['subtext'] = str(card.get('subtext') or fallback['subtext'])[:300]
            out['why_now'] = str(card.get('why_now') or fallback.get('why_now', ''))[:400]
            raw_platforms = card.get('platforms') or fallback['platforms']
            if not isinstance(raw_platforms, list):
                raw_platforms = ['x_twitter', 'youtube']
            out['platforms'] = [p for p in raw_platforms if p in valid_platforms] or ['x_twitter']
            try:
                score = int(float(card.get('composite_score') or fallback['composite_score']))
            except Exception:
                score = fallback['composite_score']
            out['composite_score'] = max(50, min(100, score))
            out['estimated_read_time'] = str(card.get('estimated_read_time') or fallback['estimated_read_time'])
            out['keywords'] = list(card.get('keywords') or fallback['keywords'])[:8]
            prompt = str(card.get('chat_input_prompt') or fallback['chat_input_prompt'])
            if len(prompt) < 100:
                prompt = fallback['chat_input_prompt']
            out['chat_input_prompt'] = prompt
            return out
        if raw_cards:
            while len(raw_cards) < 3:
                raw_cards.append(evergreen_cards[len(raw_cards) % 3])
            if excluded_topics:
                excluded_lower = {str(x).lower() for x in excluded_topics}
                filtered = [c for c in raw_cards if str(c.get('headline', '')).lower() not in excluded_lower]
                raw_cards = filtered if filtered else raw_cards
            final_cards = [sanitize_card(raw_cards[i], evergreen_cards[i]) for i in range(min(3, len(raw_cards)))]
        else:
            final_cards = [dict(c) for c in evergreen_cards]
        for i, card in enumerate(final_cards):
            card['rank'] = i + 1
        db = get_supabase_manager()
        if db:
            try:
                db.save_generation_log({
                    'user_input': 'surprise_me_v2',
                    'input_type': 'surprise_me_cards',
                    'model': DEFAULT_MODEL,
                    'template': '',
                    'tone': 'multiagent',
                    'enhanced': True,
                    'success': True,
                    'generation_time': time.time() - start_time
                }, user_id=g.user_id)
            except Exception as db_error:
                print(f"Surprise Me v2 log failed: {db_error}")
        return jsonify({'success': True, 'cards': final_cards})
    except Exception as e:
        print(f"Surprise Me v2 error: {e}")
        return jsonify({'error': "Oops! The AI got too excited. Let's try that again."}), 500


@app.route('/api/surprise-me/prompt', methods=['POST'])
@app.route('/api/surprise-me/generate-prompt', methods=['POST'])
@require_session
def surprise_me_prompt():
    try:
        start_time = time.time()
        data = request.get_json() or {}
        user_preferences = data.get('user_preferences') or {}
        topics_of_interest = user_preferences.get('topics_of_interest') or []
        excluded_topics = user_preferences.get('excluded_topics') or []
        technical_level = user_preferences.get('technical_level') or 'intermediate'
        audience = user_preferences.get('audience') or 'independent AI developers and small product teams'
        tone_value = user_preferences.get('tone') or 'two_friends'
        topic_hint = data.get('topic_hint') or user_preferences.get('topic_hint')
        current_date = datetime.now().strftime("%B %d, %Y")
        base_prompt = (
            "You are helping a human write a publication-ready Medium article about modern AI development.\n"
            "Today is " + current_date + ". Prioritize topics announced in the last 48-72 hours.\n"
            "Select one genuinely trending topic related to AI engineering, open-source tools, Python, modern agent frameworks, or workflow automation.\n"
            "Use only information that would be discoverable via real-time web search, GitHub trending (daily), the Hacker News front page, Reddit communities such as r/MachineLearning and r/LocalLLaMA, Product Hunt launches, and major AI release notes.\n"
            "If a concrete topic_hint is provided, prefer that exact tool, library, or framework as long as it is actually trending.\n"
            "Return a single JSON object only. Do not include any markdown, prose outside JSON, or explanations.\n"
            "The JSON must follow this structure strictly:\n"
            "article_metadata: object with topic, angle, source_url, source_date, publish_date, estimated_read_time, target_audience, technical_level.\n"
            "headline_options: array of 3 objects with headline text under 80 characters, each naming the specific tool and stating a concrete benefit.\n"
            "opening_hook: object with sentence_1, sentence_2, sentence_3 written as 2-3 short, conversational sentences.\n"
            "main_content_blocks: array of objects. Each object has block_type, title, purpose, and content.\n"
            "Use these block_types: what_it_is, why_now, key_features, how_it_works, real_world_use, how_it_compares.\n"
            "code_examples: array of Python-focused objects with title, language, code, and explanation. Code must be realistic and syntactically valid.\n"
            "practical_applications: array of 2-3 objects with title, scenario, inputs, and outputs.\n"
            "comparison_context: object describing at least two alternatives, their strengths, and tradeoffs.\n"
            "conclusion: object with summary, who_should_read, and next_steps (an array of 2-3 concrete actions).\n"
            "seo_keywords: object with primary_keyword, secondary_keywords, meta_description, and suggested_tags.\n"
            "Writing style: two friends talking about a specific piece of tech they just discovered. Confident, direct, specific, no corporate jargon.\n"
            "Do not include any URLs or links anywhere in the JSON. If you must reference a source, describe it generically without a URL.\n"
        )
        base_prompt += "Audience: " + str(audience) + ".\n"
        base_prompt += "Technical level: " + str(technical_level) + ".\n"
        if topics_of_interest:
            base_prompt += "User interests: " + ", ".join(str(x) for x in topics_of_interest) + ".\n"
        if excluded_topics:
            base_prompt += "Avoid these topics or tools entirely: " + ", ".join(str(x) for x in excluded_topics) + ".\n"
        if topic_hint:
            base_prompt += "Topic hint to prefer if it is trending: " + str(topic_hint) + ".\n"
        ai_result = get_ai_manager().generate_content(base_prompt, model=DEFAULT_MODEL)
        parsed = None
        try:
            parsed = json.loads(ai_result)
        except Exception:
            if isinstance(ai_result, str):
                first = ai_result.find("{")
                last = ai_result.rfind("}")
                if first != -1 and last != -1 and last > first:
                    snippet = ai_result[first : last + 1]
                    try:
                        parsed = json.loads(snippet)
                    except Exception:
                        parsed = None
        if not isinstance(parsed, dict):
            return jsonify({'error': 'Failed to build JSON prompt. Please try again.'}), 500
        sanitized = _sanitize_prompt_value(parsed)
        db = get_supabase_manager()
        if db:
            try:
                meta = sanitized.get('meta') if isinstance(sanitized, dict) else {}
                db.save_generation_log({
                    'user_input': str(meta.get('topic') if isinstance(meta, dict) else ''),
                    'input_type': 'surprise_full_prompt',
                    'model': DEFAULT_MODEL,
                    'template': '',
                    'tone': tone_value,
                    'enhanced': True,
                    'success': True,
                    'generation_time': time.time() - start_time
                })
            except Exception as db_error:
                print(f"Surprise Me full prompt log failed: {db_error}")
        return jsonify({'success': True, 'prompt': sanitized})
    except Exception as e:
        print(f"Surprise Me full prompt error: {e}")
        return jsonify({'error': "Unable to build a JSON prompt right now. Please try again."}), 500

@app.route('/generate', methods=['POST'])
@require_session
@rate_limit_check(max_requests=5, window=300)
def generate_blog():
    print("=" * 80)
    print("GENERATE BLOG ROUTE CALLED")
    print("=" * 80)
    start_time = time.time()
    
    try:
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request content type: {request.content_type}")
        
        user_input = None
        uploaded_file_content = None
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            print("Processing file upload...")
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    print(f"Uploaded file: {filename}")
                    
                    temp_path = os.path.join(tempfile.gettempdir(), filename)
                    file.save(temp_path)
                    
                    try:
                        file_content, file_type = process_uploaded_file(temp_path, filename)
                        if file_content:
                            user_input = f"Document content from {filename}:\n\n{file_content}"
                            print(f"Extracted {len(file_content)} characters from {file_type} file")
                        else:
                            return jsonify({'error': f'Could not extract text from {filename}'}), 400
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
            
            model = request.form.get('model', DEFAULT_MODEL)
            enhance = request.form.get('enhance', 'false').lower() == 'true'
            template = request.form.get('template', None)
            tone = request.form.get('tone', None)
            industry = request.form.get('industry', None)
        else:
            data = request.get_json()
            print(f"Request JSON data: {data}")
            
            user_input = data.get('youtube_link', '').strip()
            model = data.get('model', DEFAULT_MODEL)
            enhance = data.get('enhance', False)
            template = data.get('template', None)
            tone = data.get('tone', None)
            industry = data.get('industry', None)
        
        print(f"Parsed parameters:")
        print(f"  - user_input: {user_input[:100] if user_input else 'None'}")
        print(f"  - model: {model}")
        print(f"  - enhance: {enhance}")
        print(f"  - template: {template}")
        print(f"  - tone: {tone}")
        print(f"  - industry: {industry}")
        
        if not user_input:
            return jsonify({'error': 'Input is required'}), 400
        
        input_type = detect_input_type(user_input)
        
        blog_post_text = generate_blog_post_text(user_input, model, template, tone, industry)
        print(f"Generated blog post length: {len(blog_post_text) if blog_post_text else 0}")
        
        if not blog_post_text or len(blog_post_text.strip()) < 100:
            print(f"Blog post too short or empty: {blog_post_text[:100] if blog_post_text else 'None'}")
            raise Exception("Failed to generate blog content. AI response was empty or too short.")
        
        if enhance:
            print("Enhancing blog post...")
            blog_post_text = enhance_blog_post(blog_post_text)
            print(f"Enhanced blog post length: {len(blog_post_text) if blog_post_text else 0}")
        
        print("Extracting title from markdown...")
        title = extract_title_from_markdown(blog_post_text)
        print(f"Extracted title: {title}")
        
        print("Generating images...")
        try:
            images = generate_images_for_blog(title, blog_post_text)
            print(f"Images generated: {len([img for img in images if img])} of 2")
            if images[0]:
                print(f"Image 1 size: {len(images[0])} chars")
            else:
                print("Image 1 is None")
            if images[1]:
                print(f"Image 2 size: {len(images[1])} chars")
            else:
                print("Image 2 is None")
        except Exception as img_error:
            print(f"Warning: Image generation failed: {img_error}")
            import traceback
            traceback.print_exc()
            images = [None, None]
        
        print("Calculating metadata...")
        reading_time = estimate_reading_time(blog_post_text)
        print(f"Reading time: {reading_time}")
        key_quotes = extract_key_quotes(blog_post_text)
        print(f"Key quotes: {len(key_quotes) if key_quotes else 0}")
        engagement_score = calculate_engagement_score(blog_post_text)
        print(f"Engagement score: {engagement_score}")
        
        print("Analyzing SEO...")
        seo_analysis = analyze_seo(blog_post_text, title)
        print(f"SEO analysis: {seo_analysis}")
        seo_recommendations = generate_seo_recommendations(seo_analysis)
        print(f"SEO recommendations: {len(seo_recommendations) if seo_recommendations else 0}")
        
        print("Converting markdown to HTML...")
        
        cleaned_markdown = blog_post_text.replace('```', '')
        cleaned_markdown = re.sub(r'`([^`]+)`', r'\1', cleaned_markdown)
        
        blog_post_html = markdown.markdown(
            cleaned_markdown, 
            extensions=[
                "markdown.extensions.tables",
                "markdown.extensions.fenced_code",
                "markdown.extensions.nl2br",
                "markdown.extensions.codehilite",
                "markdown.extensions.extra",
                "markdown.extensions.sane_lists"
            ],
            extension_configs={
                'markdown.extensions.codehilite': {
                    'css_class': 'highlight',
                    'linenums': False
                }
            }
        )
        
        print(f"HTML conversion result length: {len(blog_post_html)}")
        
        blog_post_html = re.sub(r'<div[^>]*>', '', blog_post_html)
        blog_post_html = blog_post_html.replace('</div>', '')
        blog_post_html = re.sub(r'<pre[^>]*>', '', blog_post_html)
        blog_post_html = blog_post_html.replace('</pre>', '')
        blog_post_html = re.sub(r'<code[^>]*>', '', blog_post_html)
        blog_post_html = blog_post_html.replace('</code>', '')
        blog_post_html = re.sub(r' class="[^"]*"', '', blog_post_html)
        blog_post_html = re.sub(r' id="[^"]*"', '', blog_post_html)
        blog_post_html = re.sub(r'<p>\s*</p>', '', blog_post_html)
        blog_post_html = re.sub(r'<span[^>]*>', '', blog_post_html)
        blog_post_html = blog_post_html.replace('</span>', '')
        blog_post_html = blog_post_html.strip()
        
        print(f"Final HTML length: {len(blog_post_html)}")
        
        generation_time = time.time() - start_time
        print(f"Generation time: {generation_time:.2f}s")
        
        post_id = str(uuid.uuid4())
        temp_file = TEMP_STORAGE_DIR / f"{post_id}.json"
        print(f"Generated post_id: {post_id}")
        print(f"Temp file path: {temp_file}")
        
        reading_time_int = 0
        if reading_time:
            if isinstance(reading_time, str):
                reading_time_int = int(reading_time.split()[0])
            else:
                reading_time_int = int(reading_time)
        
        print("Analyzing Medium readiness...")
        medium_analysis = analyze_medium_readiness(blog_post_text)
        print(f"Medium readiness score: {medium_analysis.get('medium_readiness_score', 0)}")
        
        print("Preparing full blog data for storage...")
        
        image_1_data = None
        image_2_data = None
        if images and images[0]:
            img_str = str(images[0])
            if len(img_str) < 5000000:
                image_1_data = img_str
                print(f"✓ Image 1 included: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
            else:
                print(f"✗ Image 1 too large, skipping: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
        else:
            print("✗ Image 1 not generated")
        if images and images[1]:
            img_str = str(images[1])
            if len(img_str) < 5000000:
                image_2_data = img_str
                print(f"✓ Image 2 included: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
            else:
                print(f"✗ Image 2 too large, skipping: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
        else:
            print("✗ Image 2 not generated")
        
        full_blog_data = {
            'title': str(title) if title else '',
            'blog_post_html': str(blog_post_html) if blog_post_html else '',
            'blog_post_markdown': str(blog_post_text) if blog_post_text else '',
            'image_data': image_1_data,
            'image_data_2': image_2_data,
            'reading_time': reading_time,
            'key_quotes': list(key_quotes) if key_quotes else [],
            'engagement_score': int(engagement_score) if engagement_score else 0,
            'word_count': int(len(blog_post_text.split())),
            'seo_score': int(seo_analysis.get('seo_score', 0)),
            'viral_potential': int(seo_analysis.get('viral_potential', 0)),
            'readability_score': int(seo_analysis.get('readability_score', 0)),
            'seo_recommendations': list(seo_recommendations) if seo_recommendations else [],
            'medium_readiness_score': medium_analysis.get('medium_readiness_score', 0),
            'medium_recommendations': medium_analysis.get('recommendations', [])
        }
        
        print(f"Writing to temp file: {temp_file}")
        print(f"Temp directory exists: {TEMP_STORAGE_DIR.exists()}")
        print(f"Temp directory writable: {os.access(TEMP_STORAGE_DIR, os.W_OK)}")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(full_blog_data, f, ensure_ascii=False)
        
        print(f"File written successfully")
        print(f"File exists after write: {temp_file.exists()}")
        print(f"File size: {temp_file.stat().st_size if temp_file.exists() else 0} bytes")
        
        print("Attempting to save to Supabase...")
        db = get_supabase_manager()
        if db:
            print("Supabase manager available, saving blog post...")
            try:
                result = db.save_blog_post({
                    'title': title,
                    'html_content': blog_post_html,
                    'markdown_content': blog_post_text,
                    'image_header': images[0],
                    'image_content': images[1],
                    'reading_time': reading_time,
                    'key_quotes': key_quotes,
                    'engagement_score': engagement_score,
                    'word_count': len(blog_post_text.split()),
                    'seo_score': seo_analysis.get('seo_score', 0),
                    'viral_potential': seo_analysis.get('viral_potential', 0),
                    'readability_score': seo_analysis.get('readability_score', 0),
                    'seo_recommendations': seo_recommendations
                })
                if result:
                    session['db_post_id'] = result.get('id')
                    print(f"Blog post saved to Supabase successfully with ID: {result.get('id')}")
                else:
                    print("Supabase save returned None")
            except Exception as e:
                print(f"Supabase save failed (non-critical): {str(e)[:200]}")
        else:
            print("Supabase not configured, skipping database save")
        
        session.permanent = True
        session['current_post_id'] = post_id
        session['generation_params'] = {
            'user_input': user_input,
            'model': model,
            'template': template,
            'tone': tone,
            'industry': industry,
            'enhance': enhance
        }
        session.modified = True
        
        print(f"Session set with post_id: {post_id}")
        print(f"Session permanent: {session.permanent}")
        print(f"Session modified: {session.modified}")
        print(f"Session data: {dict(session)}")
        
        if db:
            try:
                db.save_generation_log({
                    'user_input': user_input,
                    'input_type': input_type,
                    'model': model,
                    'template': template,
                    'tone': tone,
                    'enhanced': enhance,
                    'success': True,
                    'generation_time': generation_time
                }, user_id=g.user_id)
                print("Generation log saved successfully")
            except Exception as db_error:
                print(f"Generation log save failed (non-critical): {str(db_error)[:200]}")
        
        response = jsonify({
            'success': True,
            'redirect': f'/blog?post_id={post_id}',
            'post_id': post_id
        })
        
        print(f"Response redirect URL: /blog?post_id={post_id}")
        print(f"Response headers before return: {dict(response.headers)}")
        print(f"Session cookie should be set in response")
        
        return response
        
    except Exception as e:
        import traceback
        print(f"ERROR in blog generation: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        
        generation_time = time.time() - start_time
        
        error_message = str(e)
        if "All AI providers failed" in error_message or "API" in error_message:
            error_message = "AI generation failed. Please check that you have at least one AI provider API key configured in your .env file (OPENAI_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY). Original error: " + error_message
        
        db = get_supabase_manager()
        if db:
            try:
                db.save_generation_log({
                    'user_input': user_input if 'user_input' in locals() else 'unknown',
                    'input_type': input_type if 'input_type' in locals() else 'unknown',
                    'model': model if 'model' in locals() else 'unknown',
                    'template': template if 'template' in locals() else None,
                    'tone': tone if 'tone' in locals() else None,
                    'enhanced': enhance if 'enhance' in locals() else False,
                    'success': False,
                    'error': str(e),
                    'generation_time': generation_time
                }, user_id=g.user_id)
            except Exception as db_error:
                print(f"Warning: Failed to save error log: {db_error}")
        
        return jsonify({'error': error_message}), 500

@app.route('/blog', methods=['GET', 'POST'])
@require_session
def blog_post():
    print(f"=" * 80)
    print(f"BLOG ROUTE CALLED - Method: {request.method}")
    print(f"=" * 80)
    
    if request.method == 'GET':
        print(f"Request cookies: {dict(request.cookies)}")
        print(f"Request headers: {dict(request.headers)}")
        
        post_id = request.args.get('post_id') or session.get('current_post_id')
        generation_params = session.get('generation_params', {})
        
        print(f"Query param post_id: {request.args.get('post_id')}")
        print(f"Session post_id: {session.get('current_post_id')}")
        print(f"Final post_id: {post_id}")
        print(f"Session keys: {list(session.keys())}")
        print(f"Session permanent: {session.permanent}")
        print(f"Full session data: {dict(session)}")
        
        if post_id:
            temp_file = TEMP_STORAGE_DIR / f"{post_id}.json"
            print(f"Looking for temp file: {temp_file}")
            print(f"Temp file exists: {temp_file.exists()}")
            if temp_file.exists():
                try:
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        blog_data = json.load(f)
                    print(f"Blog data loaded, keys: {list(blog_data.keys())}")
                    return render_template('blog-post.html', **blog_data, generation_params=generation_params)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    return redirect(url_for('index'))
                except Exception as e:
                    print(f"Error loading blog data: {e}")
                    return redirect(url_for('index'))
            else:
                print(f"Temp file not found at {temp_file}")
        else:
            print(f"No post_id in session")
        
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_input = request.form.get('youtube_link', '').strip()
        model = request.form.get('model', DEFAULT_MODEL)
        enhance = request.form.get('enhance') == 'on'
        template = request.form.get('template', None)
        tone = request.form.get('tone', None)
        print(f"Form input: {user_input[:100] if user_input else 'None'}")
        
        if not user_input:
            return render_template('index.html', error='Please enter a URL or topic')
        
        try:
            blog_post_text = generate_blog_post_text(user_input, model, template, tone)
            
            if not blog_post_text or len(blog_post_text.strip()) < 100:
                return render_template('index.html', error='Failed to generate blog content. Please try again.')
            
            if enhance:
                blog_post_text = enhance_blog_post(blog_post_text)
            
            title = extract_title_from_markdown(blog_post_text)
            
            try:
                images = generate_images_for_blog(title, blog_post_text)
            except Exception as img_error:
                print(f"Warning: Image generation failed: {img_error}")
                images = [None, None]
            
            reading_time = estimate_reading_time(blog_post_text)
            key_quotes = extract_key_quotes(blog_post_text)
            engagement_score = calculate_engagement_score(blog_post_text)
            
            seo_analysis = analyze_seo(blog_post_text, title)
            seo_recommendations = generate_seo_recommendations(seo_analysis)
            
            cleaned_markdown = blog_post_text.replace('```', '')
            cleaned_markdown = re.sub(r'`([^`]+)`', r'\1', cleaned_markdown)
            
            blog_post_html = markdown.markdown(
                cleaned_markdown,
                extensions=[
                    "markdown.extensions.tables",
                    "markdown.extensions.fenced_code",
                    "markdown.extensions.nl2br",
                    "markdown.extensions.codehilite",
                    "markdown.extensions.extra",
                    "markdown.extensions.sane_lists"
                ],
                extension_configs={
                    'markdown.extensions.codehilite': {
                        'css_class': 'highlight',
                        'linenums': False
                    }
                }
            )
            
            blog_post_html = re.sub(r'<div[^>]*>', '', blog_post_html)
            blog_post_html = blog_post_html.replace('</div>', '')
            blog_post_html = re.sub(r'<pre[^>]*>', '', blog_post_html)
            blog_post_html = blog_post_html.replace('</pre>', '')
            blog_post_html = re.sub(r'<code[^>]*>', '', blog_post_html)
            blog_post_html = blog_post_html.replace('</code>', '')
            blog_post_html = re.sub(r' class="[^"]*"', '', blog_post_html)
            blog_post_html = re.sub(r' id="[^"]*"', '', blog_post_html)
            blog_post_html = re.sub(r'<p>\s*</p>', '', blog_post_html)
            blog_post_html = re.sub(r'<span[^>]*>', '', blog_post_html)
            blog_post_html = blog_post_html.replace('</span>', '')
            blog_post_html = blog_post_html.strip()
            
            post_id = str(uuid.uuid4())
            temp_file = TEMP_STORAGE_DIR / f"{post_id}.json"
            
            reading_time_int = 0
            if reading_time:
                if isinstance(reading_time, str):
                    reading_time_int = int(reading_time.split()[0])
                else:
                    reading_time_int = int(reading_time)
            
            medium_analysis = analyze_medium_readiness(blog_post_text)
            
            image_1_data = None
            image_2_data = None
            if images and images[0]:
                img_str = str(images[0])
                if len(img_str) < 5000000:
                    image_1_data = img_str
                    print(f"✓ Image 1 included: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
                else:
                    print(f"✗ Image 1 too large: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
            else:
                print("✗ Image 1 not generated")
            if images and images[1]:
                img_str = str(images[1])
                if len(img_str) < 5000000:
                    image_2_data = img_str
                    print(f"✓ Image 2 included: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
                else:
                    print(f"✗ Image 2 too large: {len(img_str)} chars ({len(img_str)/1000000:.2f}MB)")
            else:
                print("✗ Image 2 not generated")
            
            full_blog_data = {
                'title': str(title) if title else '',
                'blog_post_html': str(blog_post_html) if blog_post_html else '',
                'blog_post_markdown': str(blog_post_text) if blog_post_text else '',
                'image_data': image_1_data,
                'image_data_2': image_2_data,
                'reading_time': reading_time,
                'key_quotes': list(key_quotes) if key_quotes else [],
                'engagement_score': int(engagement_score) if engagement_score else 0,
                'word_count': int(len(blog_post_text.split())),
                'seo_score': int(seo_analysis.get('seo_score', 0)),
                'viral_potential': int(seo_analysis.get('viral_potential', 0)),
                'readability_score': int(seo_analysis.get('readability_score', 0)),
                'seo_recommendations': list(seo_recommendations) if seo_recommendations else [],
                'medium_readiness_score': medium_analysis.get('medium_readiness_score', 0),
                'medium_recommendations': medium_analysis.get('recommendations', [])
            }
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(full_blog_data, f, ensure_ascii=False)
            
            db = get_supabase_manager()
            if db:
                try:
                    result = db.save_blog_post({
                        'title': title,
                        'html_content': blog_post_html,
                        'markdown_content': blog_post_text,
                        'image_header': images[0],
                        'image_content': images[1],
                        'reading_time': reading_time,
                        'key_quotes': key_quotes,
                        'engagement_score': engagement_score,
                        'word_count': len(blog_post_text.split()),
                        'seo_score': seo_analysis.get('seo_score', 0),
                        'viral_potential': seo_analysis.get('viral_potential', 0),
                        'readability_score': seo_analysis.get('readability_score', 0),
                        'seo_recommendations': seo_recommendations,
                        'medium_readiness_score': medium_analysis.get('medium_readiness_score', 0),
                        'medium_recommendations': medium_analysis.get('recommendations', [])
                    }, user_id=g.user_id)
                    if result:
                        print(f"Supabase save successful")
                except Exception as e:
                    print(f"Supabase save failed (non-critical): {str(e)[:200]}")
            
            session['current_post_id'] = post_id
            
            return redirect(url_for('blog_post'))
        except Exception as e:
            return render_template('index.html', error=str(e))
    
    return render_template('index.html')

@app.route('/export', methods=['POST'])
@require_session
def export_markdown():
    data = request.get_json()
    markdown_content = data.get('markdown', '')
    return jsonify({
        'success': True,
        'content': markdown_content
    })

@app.route('/health')
def health():
    db = get_supabase_manager()
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if db else 'not_configured',
        'temp_storage': str(TEMP_STORAGE_DIR),
        'temp_files_count': len(list(TEMP_STORAGE_DIR.glob('*.json')))
    }
    return jsonify(status), 200

@app.route('/auth/medium')
@require_session
def auth_medium():
    try:
        state = str(uuid.uuid4())
        nonce = hashlib.sha256(os.urandom(32)).hexdigest()
        session['oauth_state'] = state
        session['oauth_nonce'] = nonce
        session.permanent = True
        
        medium_auth = get_medium_auth()
        auth_url = medium_auth.get_auth_url(state)
        return redirect(auth_url)
    except Exception as e:
        print(f"Medium auth error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/auth/medium/callback')
@require_session
def auth_medium_callback():
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            print(f"Medium OAuth error: {error}")
            return jsonify({'error': 'OAuth error from Medium'}), 400
        
        if not code:
            return jsonify({'error': 'Missing authorization code'}), 400
        
        stored_state = session.get('oauth_state')
        if not stored_state or state != stored_state:
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        medium_auth = get_medium_auth()
        token_data = medium_auth.exchange_code_for_token(code)
        
        if not token_data:
            return jsonify({'error': 'Failed to exchange code for token'}), 400
        
        user_info = medium_auth.get_user_info(token_data['access_token'])
        if not user_info:
            return jsonify({'error': 'Failed to get user info'}), 400
        
        user_id = g.user_id
        account_manager = get_social_account_manager()
        
        account_data = {
            'user_info': user_info,
            'access_token': token_data['access_token'],
            'token_type': token_data.get('token_type'),
            'expires_at': token_data.get('expires_at')
        }
        
        account_manager.save_account(user_id, 'medium', account_data)
        session['medium_connected'] = True
        
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Medium callback error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/auth/linkedin')
@require_session
def auth_linkedin():
    try:
        state = str(uuid.uuid4())
        nonce = hashlib.sha256(os.urandom(32)).hexdigest()
        session['oauth_state'] = state
        session['oauth_nonce'] = nonce
        session.permanent = True
        
        linkedin_auth = get_linkedin_auth()
        auth_url = linkedin_auth.get_auth_url(state)
        return redirect(auth_url)
    except Exception as e:
        print(f"LinkedIn auth error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/auth/linkedin/callback')
@require_session
def auth_linkedin_callback():
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            print(f"LinkedIn OAuth error: {error}")
            return jsonify({'error': 'OAuth error from LinkedIn'}), 400
        
        if not code:
            return jsonify({'error': 'Missing authorization code'}), 400
        
        stored_state = session.get('oauth_state')
        if not stored_state or state != stored_state:
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        linkedin_auth = get_linkedin_auth()
        token_data = linkedin_auth.exchange_code_for_token(code)
        
        if not token_data:
            return jsonify({'error': 'Failed to exchange code for token'}), 400
        
        user_info = linkedin_auth.get_user_info(token_data['access_token'])
        if not user_info:
            return jsonify({'error': 'Failed to get user info'}), 400
        
        user_id = g.user_id
        account_manager = get_social_account_manager()
        
        account_data = {
            'user_info': user_info,
            'access_token': token_data['access_token'],
            'token_type': token_data.get('token_type'),
            'expires_at': token_data.get('expires_at')
        }
        
        account_manager.save_account(user_id, 'linkedin', account_data)
        session['linkedin_connected'] = True
        
        return redirect(url_for('index'))
    except Exception as e:
        print(f"LinkedIn callback error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/social/accounts')
@require_session
def get_social_accounts():
    try:
        user_id = g.user_id
        if not user_id:
            return jsonify({'error': 'Session required'}), 401
        
        account_manager = get_social_account_manager()
        accounts = account_manager.list_accounts(user_id)
        
        return jsonify({
            'success': True,
            'accounts': accounts
        })
    except Exception as e:
        print(f"Get accounts error: {e}")
        return jsonify({'error': 'Failed to retrieve accounts'}), 500

@app.route('/api/social/disconnect/<platform>', methods=['POST'])
@require_session
def disconnect_social(platform):
    try:
        if platform not in ['medium', 'linkedin']:
            return jsonify({'error': 'Invalid platform'}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Session required'}), 401
        
        account_manager = get_social_account_manager()
        
        if account_manager.delete_account(user_id, platform):
            session[f'{platform}_connected'] = False
            return jsonify({'success': True})
        
        return jsonify({'error': 'Failed to disconnect'}), 400
    except Exception as e:
        print(f"Disconnect error: {e}")
        return jsonify({'error': 'Failed to disconnect account'}), 500

@app.route('/api/social/publish', methods=['POST'])
@require_session
def publish_to_social():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        
        platforms = data.get('platforms', [])
        if not platforms or not isinstance(platforms, list):
            return jsonify({'error': 'Invalid platforms'}), 400
        
        for platform in platforms:
            if platform not in ['medium', 'linkedin']:
                return jsonify({'error': f'Invalid platform: {platform}'}), 400
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        html_content = data.get('html_content', '').strip()
        image_url = data.get('image_url', '').strip() if data.get('image_url') else None
        tags = data.get('tags', [])
        
        if not title or not content:
            return jsonify({'error': 'Title and content required'}), 400
        
        if len(title) > 500:
            return jsonify({'error': 'Title too long'}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Session required'}), 401
        
        account_manager = get_social_account_manager()
        results = {}
        
        if 'medium' in platforms:
            medium_account = account_manager.get_account(user_id, 'medium')
            if medium_account:
                medium_auth = get_medium_auth()
                result = medium_auth.publish_post(
                    medium_account['access_token'],
                    title,
                    html_content,
                    tags=tags,
                    image_url=image_url
                )
                results['medium'] = result
                account_manager.update_last_used(user_id, 'medium')
            else:
                results['medium'] = {'success': False, 'error': 'Account not connected'}
        
        if 'linkedin' in platforms:
            linkedin_account = account_manager.get_account(user_id, 'linkedin')
            if linkedin_account:
                linkedin_auth = get_linkedin_auth()
                result = linkedin_auth.share_post(
                    linkedin_account['access_token'],
                    content,
                    image_url=image_url
                )
                results['linkedin'] = result
                account_manager.update_last_used(user_id, 'linkedin')
            else:
                results['linkedin'] = {'success': False, 'error': 'Account not connected'}
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        print(f"Publish error: {e}")
        return jsonify({'error': 'Publishing failed'}), 500

@app.route('/api/seo-analysis', methods=['POST'])
def seo_analysis():
    try:
        data = request.get_json()
        text = data.get('text', '')
        title = data.get('title', '')
        
        analysis = analyze_seo(text, title)
        recommendations = generate_seo_recommendations(analysis)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/title-alternatives', methods=['POST'])
def title_alternatives():
    try:
        data = request.get_json()
        current_title = data.get('title', '')
        content = data.get('content', '')
        
        prompt = get_title_alternatives_prompt(current_title, content)
        alternatives = get_ai_manager().generate_content(prompt)
        
        return jsonify({
            'success': True,
            'alternatives': alternatives
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meta-description', methods=['POST'])
def meta_description():
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        
        prompt = get_meta_description_prompt(title, content)
        description = get_ai_manager().generate_content(prompt)
        
        return jsonify({
            'success': True,
            'meta_description': description
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rewrite-section', methods=['POST'])
def rewrite_section():
    try:
        data = request.get_json()
        section = data.get('section', '')
        instruction = data.get('instruction', 'improve this section')
        
        prompt = get_section_rewrite_prompt(section, instruction)
        rewritten = get_ai_manager().generate_content(prompt)
        
        return jsonify({
            'success': True,
            'rewritten': rewritten
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/adjust-tone', methods=['POST'])
def adjust_tone():
    try:
        data = request.get_json()
        content = data.get('content', '')
        target_tone = data.get('tone', 'professional')
        
        prompt = get_tone_adjustment_prompt(content, target_tone)
        adjusted = get_ai_manager().generate_content(prompt)
        
        return jsonify({
            'success': True,
            'adjusted': adjusted
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expand-section', methods=['POST'])
def expand_section():
    try:
        data = request.get_json()
        section = data.get('section', '')
        target_words = data.get('target_words', None)
        
        prompt = get_expand_prompt(section, target_words)
        expanded = get_ai_manager().generate_content(prompt)
        
        return jsonify({
            'success': True,
            'expanded': expanded
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compress-section', methods=['POST'])
def compress_section():
    try:
        data = request.get_json()
        section = data.get('section', '')
        target_words = data.get('target_words', None)
        
        prompt = get_compress_prompt(section, target_words)
        compressed = get_ai_manager().generate_content(prompt)
        
        return jsonify({
            'success': True,
            'compressed': compressed
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-storyboard', methods=['POST'])
def generate_storyboard():
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        
        if not title or not content:
            return jsonify({'error': 'Title and content required'}), 400
        
        from prompts import get_storyboard_diagram_prompt
        
        prompt = get_storyboard_diagram_prompt(title, content[:1000])
        print(f"[STORYBOARD] Generating diagram for: {title[:50]}")
        
        storyboard_image = get_ai_manager().generate_images(prompt, None)
        
        if storyboard_image and storyboard_image[0]:
            return jsonify({
                'success': True,
                'image': storyboard_image[0]
            })
        else:
            return jsonify({'error': 'Failed to generate storyboard'}), 500
    except Exception as e:
        print(f"[STORYBOARD] Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-diagram', methods=['POST'])
def generate_diagram():
    """
    Generate flowcharts, mind maps, or infographics from blog content.
    Uses AI to create Mermaid diagrams and renders them as images.
    """
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        diagram_type = data.get('type', 'flowchart')  # flowchart, mindmap, process, infographic
        
        if not title or not content:
            return jsonify({'error': 'Title and content required'}), 400
        
        if diagram_type not in ['flowchart', 'mindmap', 'process', 'infographic']:
            return jsonify({'error': 'Invalid diagram type'}), 400
        
        print(f"[DIAGRAM] Generating {diagram_type} for: {title[:50]}")
        
        # Get diagram generator with AI manager
        diagram_gen = get_diagram_generator(get_ai_manager())
        
        # Generate diagram
        result = diagram_gen.generate_flowchart_from_content(title, content, diagram_type)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error', 'Failed to generate diagram')}), 500
            
    except Exception as e:
        print(f"[DIAGRAM] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-linkedin', methods=['POST'])
def generate_linkedin():
    try:
        data = request.get_json()
        medium_title = data.get('title', '')
        medium_content = data.get('content', '')
        
        if not medium_title or not medium_content:
            return jsonify({'error': 'Title and content required'}), 400
        
        ai_manager = get_ai_manager()
        linkedin_post = generate_linkedin_post(medium_title, medium_content, ai_manager)
        
        if not linkedin_post:
            return jsonify({'error': 'Failed to generate LinkedIn post'}), 500
        
        return jsonify({
            'success': True,
            'linkedin_post': linkedin_post
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github-info', methods=['POST'])
def github_info():
    try:
        data = request.get_json()
        github_url = data.get('url', '')
        
        if not github_url or 'github.com' not in github_url:
            return jsonify({'error': 'Valid GitHub URL required'}), 400
        
        github = get_github_handler()
        repo_info = github.get_repo_info(github_url)
        readme = github.get_readme(github_url)
        
        return jsonify({
            'success': True,
            'repo_info': repo_info,
            'readme': readme
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<format>', methods=['POST'])
def export_content(format):
    try:
        data = request.get_json()
        markdown = data.get('markdown', '')
        title = data.get('title', '')
        tags = data.get('tags', [])
        
        if format == 'medium':
            exported = export_to_medium(markdown, title)
        elif format == 'devto':
            exported = export_to_devto(markdown, title, tags)
        elif format == 'hashnode':
            exported = export_to_hashnode(markdown, title, tags)
        elif format == 'linkedin':
            exported = export_to_linkedin(markdown, title)
        elif format == 'substack':
            exported = export_to_substack(markdown, title)
        elif format == 'ghost':
            exported = export_to_ghost(markdown, title, tags)
        elif format == 'twitter':
            exported = create_twitter_thread(markdown, title)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
        
        return jsonify({
            'success': True,
            'exported': exported,
            'format': format
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates')
def get_templates():
    return jsonify({
        'success': True,
        'templates': {k: v['name'] for k, v in TEMPLATES.items()},
        'tones': list(TONE_PRESETS.keys())
    })

@app.route('/library')
@require_session
def library():
    return render_template('library.html', user=g.user)

@app.route('/batch')
@require_session
def batch():
    return render_template('batch.html', user=g.user)

@app.route('/history')
@require_session
def history():
    db = get_supabase_manager()
    if db:
        posts = db.get_recent_posts(user_id=g.user_id, limit=50)
    else:
        posts = get_all_temp_posts()
    
    print(f"History route: Found {len(posts) if posts else 0} posts")
    if posts:
        print(f"First post: {posts[0].get('title', 'No title')}")
    
    return render_template('history.html', posts=posts if posts else [], user=g.user)

@app.route('/api/posts/recent')
@require_session
def api_recent_posts():
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    posts = db.get_recent_posts(user_id=g.user_id, limit=20)
    return jsonify({'success': True, 'posts': posts})

@app.route('/api/posts/<post_id>')
@require_session
def api_get_post(post_id):
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    post = db.get_blog_post_by_id(post_id, user_id=g.user_id)
    if post:
        return jsonify({'success': True, 'post': post})
    return jsonify({'error': 'Post not found'}), 404

@app.route('/post/<post_id>')
def view_post(post_id):
    db = get_supabase_manager()
    blog_data = None
    
    if db:
        post = db.get_blog_post_by_id(post_id)
        if post:
            blog_data = {
                'title': post.get('title'),
                'blog_post_html': post.get('html_content'),
                'blog_post_markdown': post.get('markdown_content'),
                'image_data': post.get('image_header'),
                'image_data_2': post.get('image_content'),
                'reading_time': post.get('reading_time'),
                'key_quotes': post.get('key_quotes', []),
                'engagement_score': post.get('engagement_score'),
                'word_count': post.get('word_count'),
                'seo_score': post.get('seo_score'),
                'viral_potential': post.get('viral_potential'),
                'readability_score': post.get('readability_score'),
                'seo_recommendations': post.get('seo_recommendations', [])
            }
    else:
        temp_file = TEMP_STORAGE_DIR / f"{post_id}.json"
        if temp_file.exists():
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    blog_data = json.load(f)
            except Exception as e:
                print(f"Error reading temp file: {e}")
    
    if not blog_data:
        return redirect(url_for('history'))
    
    return render_template('blog-post.html', **blog_data)

@app.route('/api/posts/<post_id>/delete', methods=['DELETE'])
@require_session
def delete_post(post_id):
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    success = db.delete_post(post_id, user_id=g.user_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete post'}), 500

@app.route('/analytics')
@require_session
def analytics():
    db = get_supabase_manager()
    if db:
        blog_analytics = db.get_analytics(user_id=g.user_id)
        gen_stats = db.get_generation_stats(user_id=g.user_id)
    else:
        blog_analytics = calculate_temp_analytics()
        gen_stats = None
    
    print(f"Analytics route: analytics={blog_analytics is not None}, gen_stats={gen_stats is not None}")
    
    return render_template('analytics.html', analytics=blog_analytics, gen_stats=gen_stats, user=g.user)

@app.route('/api/analytics')
@require_session
def api_analytics():
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    blog_analytics = db.get_analytics(user_id=g.user_id)
    gen_stats = db.get_generation_stats(user_id=g.user_id)
    
    return jsonify({
        'success': True,
        'blog_analytics': blog_analytics,
        'generation_stats': gen_stats
    })

@app.route('/api/generation-stats')
@require_session
def api_generation_stats():
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    stats = db.get_generation_stats(user_id=g.user_id)
    if stats:
        return jsonify({'success': True, **stats})
    return jsonify({'success': True, 'top_model': None, 'total_generations': 0})

@app.route('/api/search')
@require_session
def api_search_posts():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    results = db.search_posts(query, user_id=g.user_id)
    return jsonify({'success': True, 'results': results})

@app.route('/api/drafts', methods=['GET', 'POST'])
@require_session
@rate_limit_check(max_requests=20, window=60)
def api_drafts():
    if request.method == 'POST':
        data = request.get_json()
        draft_id = str(uuid.uuid4())
        draft_data = {
            'id': draft_id,
            'title': data.get('title', 'Untitled Draft'),
            'content': data.get('content', ''),
            'source_url': data.get('source_url', ''),
            'source_type': data.get('source_type', ''),
            'template': data.get('template', ''),
            'tone': data.get('tone', ''),
            'model': data.get('model', ''),
            'is_auto_save': data.get('is_auto_save', False),
            'metadata': data.get('metadata', {})
        }
        save_draft(draft_data)
        return jsonify({'success': True, 'draft_id': draft_id})
    else:
        drafts = get_all_drafts()
        return jsonify({'success': True, 'drafts': drafts})

@app.route('/api/drafts/<draft_id>', methods=['GET', 'PUT', 'DELETE'])
@require_session
def api_draft_detail(draft_id):
    if request.method == 'GET':
        draft = get_draft(draft_id)
        if draft:
            return jsonify({'success': True, 'draft': draft})
        return jsonify({'error': 'Draft not found'}), 404
    elif request.method == 'PUT':
        data = request.get_json()
        draft_data = {
            'id': draft_id,
            'title': data.get('title', 'Untitled Draft'),
            'content': data.get('content', ''),
            'source_url': data.get('source_url', ''),
            'source_type': data.get('source_type', ''),
            'template': data.get('template', ''),
            'tone': data.get('tone', ''),
            'model': data.get('model', ''),
            'is_auto_save': data.get('is_auto_save', False),
            'metadata': data.get('metadata', {})
        }
        save_draft(draft_data)
        return jsonify({'success': True})
    else:
        delete_draft(draft_id)
        return jsonify({'success': True})

@app.route('/api/posts/<post_id>/versions', methods=['GET', 'POST'])
@require_session
def api_post_versions(post_id):
    if request.method == 'POST':
        data = request.get_json()
        version_data = {
            'title': data.get('title', ''),
            'markdown_content': data.get('markdown_content', ''),
            'html_content': data.get('html_content', ''),
            'word_count': data.get('word_count', 0),
            'change_description': data.get('change_description', 'Manual save')
        }
        version_number = save_post_version(post_id, version_data)
        return jsonify({'success': True, 'version_number': version_number})
    else:
        versions = get_post_versions(post_id)
        return jsonify({'success': True, 'versions': versions})

@app.route('/api/posts/<post_id>/versions/<int:version_number>')
@require_session
def api_get_version(post_id, version_number):
    version = get_post_version(post_id, version_number)
    if version:
        return jsonify({'success': True, 'version': version})
    return jsonify({'error': 'Version not found'}), 404

@app.route('/api/schedule', methods=['GET', 'POST'])
@require_session
@rate_limit_check(max_requests=20, window=60)
def api_schedule():
    if request.method == 'POST':
        data = request.get_json()
        schedule_id = str(uuid.uuid4())
        schedule_data = {
            'id': schedule_id,
            'post_id': data.get('post_id'),
            'scheduled_time': data.get('scheduled_time'),
            'publish_to': data.get('publish_to', 'medium')
        }
        schedule_post(schedule_data)
        return jsonify({'success': True, 'schedule_id': schedule_id})
    else:
        status = request.args.get('status', 'scheduled')
        scheduled = get_scheduled_posts(status)
        return jsonify({'success': True, 'scheduled_posts': scheduled})

@app.route('/api/schedule/<schedule_id>', methods=['DELETE'])
@require_session
def api_cancel_schedule(schedule_id):
    delete_scheduled_post(schedule_id)
    return jsonify({'success': True})

@app.route('/api/jobs/<job_id>/status')
@require_session
def api_job_status(job_id):
    queue = get_job_queue()
    status = queue.get_job_status(job_id)
    if status:
        return jsonify({'success': True, 'job': status})
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
@require_session
def api_cancel_job(job_id):
    queue = get_job_queue()
    cancelled = queue.cancel_job(job_id)
    if cancelled:
        return jsonify({'success': True})
    return jsonify({'error': 'Job cannot be cancelled'}), 400

@app.route('/api/jobs/stats')
@require_session
def api_job_stats():
    queue = get_job_queue()
    stats = queue.get_queue_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/cache/clear', methods=['POST'])
@rate_limit_check(max_requests=5, window=300)
def api_clear_cache():
    cache = get_cache_manager()
    cache.clear_all()
    return jsonify({'success': True, 'message': 'Cache cleared'})

@app.route('/api/progress/<job_id>')
@require_session
def api_progress(job_id):
    tracker = get_progress_tracker()
    progress = tracker.get_progress(job_id)
    if progress:
        return jsonify({'success': True, 'progress': progress})
    return jsonify({'error': 'Progress not found'}), 404

@app.route('/api/progress/<job_id>/stream')
@require_session
def api_progress_stream(job_id):
    def generate():
        tracker = get_progress_tracker()
        max_checks = 300
        check_count = 0
        
        while check_count < max_checks:
            progress = tracker.get_progress(job_id)
            if progress:
                yield f"data: {json.dumps(progress)}\n\n"
                
                if progress.get('progress', 0) >= 100:
                    break
            else:
                yield f"data: {json.dumps({'stage': 'waiting', 'progress': 0, 'message': 'Waiting for progress...'})}\n\n"
            
            time.sleep(1)
            check_count += 1
        
        yield f"data: {json.dumps({'stage': 'done', 'progress': 100, 'message': 'Complete'})}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')

@app.route('/kario-socials')
@require_session
def kario_socials():
    return render_template('kario-socials.html', user=g.user)

@app.route('/api/social-generate', methods=['POST'])
@rate_limit_check(max_requests=20, window=300)
def api_social_generate():
    try:
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')
        platforms = data.get('platforms', [])
        
        from social_automation import get_social_automation
        social = get_social_automation()
        
        ai_manager = get_ai_manager()
        
        platform = platforms[0] if platforms else 'twitter'
        generated_content = social.generate_platform_content(title, content, platform, ai_manager)
        
        return jsonify({'success': True, 'generated_content': generated_content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/social-publish', methods=['POST'])
@rate_limit_check(max_requests=10, window=300)
def api_social_publish():
    try:
        data = request.json
        content = data.get('content', '')
        platforms = data.get('platforms', [])
        
        if not content or not platforms:
            return jsonify({'success': False, 'error': 'Content and platforms required'}), 400
        
        from social_automation import get_social_automation
        social = get_social_automation()
        
        result = social.publish_to_multiple_platforms(platforms, content)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/social-schedule', methods=['POST'])
@rate_limit_check(max_requests=20, window=300)
def api_social_schedule():
    try:
        data = request.json
        content = data.get('content', '')
        platforms = data.get('platforms', [])
        date = data.get('date', '')
        time = data.get('time', '')
        
        if not all([content, platforms, date, time]):
            return jsonify({'success': False, 'error': 'All fields required'}), 400
        
        from datetime import datetime
        scheduled_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        
        from social_automation import get_social_automation
        social = get_social_automation()
        
        results = []
        for platform in platforms:
            result = social.schedule_post(platform, content, scheduled_time)
            results.append(result)
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/social-platforms-status')
def api_social_platforms_status():
    try:
        from social_automation import get_social_automation
        social = get_social_automation()
        status = social.get_all_platforms_status()
        return jsonify({'success': True, 'platforms': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    scheduler = get_scheduler()
    scheduler.start()
    
    queue = get_job_queue()
    
    server_port = int(os.environ.get('PORT', '8000'))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    print("=" * 60)
    print("REGISTERED ROUTES:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint:30s} {rule.rule:50s} {list(rule.methods)}")
    print("=" * 60)
    print(f"Starting Flask app on port {server_port}")
    print("=" * 60)
    
    try:
        app.run(debug=debug_mode, port=server_port, host='0.0.0.0')
    finally:
        scheduler.stop()
        queue.shutdown()
