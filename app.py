import os
import base64
import markdown
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
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
    convert_mermaid_to_html
)
from ai_providers import AIProviderManager, get_youtube_transcript, detect_input_type, scrape_web_content, research_trending_topic
from seo_analyzer import analyze_seo, generate_seo_recommendations
from content_templates import TEMPLATES, TONE_PRESETS, get_template_prompt
from export_handler import export_to_medium, export_to_devto, export_to_hashnode, export_to_linkedin, export_to_substack, export_to_ghost, create_twitter_thread
from ai_editor import get_section_rewrite_prompt, get_tone_adjustment_prompt, get_expand_prompt, get_compress_prompt, get_title_alternatives_prompt, get_meta_description_prompt
from medium_research_agent import apply_medium_practices_to_prompt, optimize_content_structure, analyze_medium_readiness
from linkedin_agent import generate_linkedin_post
from github_handler import get_github_handler
from social_auth import get_medium_auth, get_linkedin_auth
from social_storage import get_social_account_manager
from supabase_client import get_supabase_manager
import time
import json
import uuid
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
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_NAME'] = '__Host-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['PREFERRED_URL_SCHEME'] = 'https' if os.environ.get('FLASK_ENV') == 'production' else 'http'

print(f"Flask app name: {app.name}")
print(f"Flask root path: {app.root_path}")
print(f"Template folder: {app.template_folder}")

ai_manager = None

DEFAULT_MODEL = 'gpt-4o'

def require_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            session.permanent = True
        return f(*args, **kwargs)
    return decorated_function

def validate_request_signature(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            signature = request.headers.get('X-Request-Signature')
            if not signature:
                return jsonify({'error': 'Missing request signature'}), 401
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id', 'anonymous')
        rate_key = f"rate_limit:{user_id}:{request.endpoint}"
        
        return f(*args, **kwargs)
    return decorated_function

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

@app.route('/', methods=['GET'])
def index():
    print("Index route called!")
    return render_template('index.html')

def generate_images_for_blog(blog_title, blog_content):
    try:
        prompt1 = prompts.get_image_gen_prompt(blog_title)
        prompt2 = prompts.get_content_image_prompt(blog_title, blog_content)
        images = get_ai_manager().generate_images(prompt1, prompt2)
        return images
    except Exception as e:
        print(f"Image generation error: {e}")
        return [None, None]

def generate_blog_post_text(user_input, model, template=None, tone=None, industry=None):
    try:
        input_type = detect_input_type(user_input)
        print(f"Input type detected: {input_type}")
        
        if input_type == 'youtube':
            try:
                content_context = get_youtube_transcript(user_input)
            except Exception as yt_error:
                print(f"YouTube extraction failed: {yt_error}")
                content_context = f"YouTube Video: {user_input}\n\nNote: Unable to extract transcript. Creating content based on the video URL. Please provide additional context if needed.\n\nGenerate a comprehensive blog post based on typical content for this type of video."
        elif input_type == 'github':
            github = get_github_handler()
            readme = github.get_readme(user_input)
            if readme:
                content_context = f"GitHub Repository Content:\n\n{readme}"
            else:
                content_context = f"GitHub Repository: {user_input}\n\nCreate content based on this GitHub repository."
        elif input_type == 'url':
            try:
                content_context = scrape_web_content(user_input)
            except Exception as url_error:
                print(f"URL scraping failed: {url_error}")
                content_context = f"Web URL: {user_input}\n\nNote: Unable to scrape content. Create a blog post based on the URL topic."
        else:
            if any(keyword in user_input.lower() for keyword in ['trending', 'latest', 'today', 'recent', 'current']):
                content_context = research_trending_topic(user_input, get_ai_manager())
            else:
                content_context = f"User Request: {user_input}\n\nCreate comprehensive, well-researched content based on this topic or prompt."
        
        print(f"Content context prepared: {len(content_context)} chars")
        
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
        
        return optimized_content
    except Exception as e:
        print(f"Exception in generate_blog_post_text: {str(e)}")
        raise Exception(f"Failed to generate blog post: {str(e)}")

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

@app.route('/generate', methods=['POST'])
def generate_blog():
    print("=" * 80)
    print("GENERATE BLOG ROUTE CALLED")
    print("=" * 80)
    start_time = time.time()
    
    try:
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request content type: {request.content_type}")
        
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
        except Exception as img_error:
            print(f"Warning: Image generation failed: {img_error}")
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
        
        blog_post_with_mermaid = convert_mermaid_to_html(blog_post_text)
        blog_post_html = markdown.markdown(
            blog_post_with_mermaid, 
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
        
        generation_time = time.time() - start_time
        print(f"Generation time: {generation_time:.2f}s")
        
        print("Converting markdown to HTML...")
        
        blog_data = {
            'title': title,
            'blog_post_html': blog_post_html,
            'blog_post_markdown': blog_post_text,
            'image_data': images[0],
            'image_data_2': images[1],
            'reading_time': reading_time,
            'key_quotes': key_quotes,
            'engagement_score': engagement_score,
            'word_count': len(blog_post_text.split()),
            'seo_score': seo_analysis.get('seo_score', 0),
            'viral_potential': seo_analysis.get('viral_potential', 0),
            'readability_score': seo_analysis.get('readability_score', 0),
            'seo_recommendations': seo_recommendations
        }
        
        print(f"Blog data prepared with {len(blog_data)} fields")
        
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
        full_blog_data = {
            'title': str(title) if title else '',
            'blog_post_html': str(blog_post_html) if blog_post_html else '',
            'blog_post_markdown': str(blog_post_text) if blog_post_text else '',
            'image_data': str(images[0]) if images[0] else None,
            'image_data_2': str(images[1]) if images[1] else None,
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
                db.save_blog_post({
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
                print("Blog post saved to Supabase successfully")
            except Exception as e:
                print(f"Database save error: {e}")
        else:
            print("Supabase manager not available (not configured)")
        
        session['current_post_id'] = post_id
        session.permanent = True
        
        session['generation_params'] = {
            'user_input': user_input,
            'model': model,
            'template': template,
            'tone': tone,
            'industry': industry,
            'enhance': enhance
        }
        
        print(f"Session set with post_id: {post_id}")
        print(f"Temp file path: {temp_file}")
        print(f"Temp file exists: {temp_file.exists()}")
        
        db = get_supabase_manager()
        if db:
            try:
                saved_post = db.save_blog_post(blog_data)
                if saved_post:
                    session['db_post_id'] = saved_post.get('id')
            except Exception as db_error:
                print(f"Warning: Failed to save to database: {db_error}")
            
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
                })
            except Exception as db_error:
                print(f"Warning: Failed to save generation log: {db_error}")
        
        return jsonify({
            'success': True,
            'redirect': '/blog'
        })
        
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
                })
            except Exception as db_error:
                print(f"Warning: Failed to save error log: {db_error}")
        
        return jsonify({'error': error_message}), 500

@app.route('/blog', methods=['GET', 'POST'])
def blog_post():
    print(f"Blog post route called! Method: {request.method}")
    
    if request.method == 'GET':
        post_id = session.get('current_post_id')
        generation_params = session.get('generation_params', {})
        print(f"Blog GET - post_id from session: {post_id}")
        print(f"Session keys: {list(session.keys())}")
        
        if post_id:
            temp_file = TEMP_STORAGE_DIR / f"{post_id}.json"
            print(f"Looking for temp file: {temp_file}")
            print(f"Temp file exists: {temp_file.exists()}")
            if temp_file.exists():
                with open(temp_file, 'r', encoding='utf-8') as f:
                    blog_data = json.load(f)
                print(f"Blog data loaded, keys: {list(blog_data.keys())}")
                return render_template('blog-post.html', **blog_data, generation_params=generation_params)
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
            
            blog_post_with_mermaid = convert_mermaid_to_html(blog_post_text)
            blog_post_html = markdown.markdown(
                blog_post_with_mermaid,
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
            
            post_id = str(uuid.uuid4())
            temp_file = TEMP_STORAGE_DIR / f"{post_id}.json"
            
            reading_time_int = 0
            if reading_time:
                if isinstance(reading_time, str):
                    reading_time_int = int(reading_time.split()[0])
                else:
                    reading_time_int = int(reading_time)
            
            medium_analysis = analyze_medium_readiness(blog_post_text)
            
            full_blog_data = {
                'title': str(title) if title else '',
                'blog_post_html': str(blog_post_html) if blog_post_html else '',
                'blog_post_markdown': str(blog_post_text) if blog_post_text else '',
                'image_data': str(images[0]) if images[0] else None,
                'image_data_2': str(images[1]) if images[1] else None,
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
                    db.save_blog_post({
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
                    })
                except Exception as e:
                    print(f"Database save error: {e}")
            
            session['current_post_id'] = post_id
            
            return redirect(url_for('blog_post'))
        except Exception as e:
            return render_template('index.html', error=str(e))
    
    return render_template('index.html')

@app.route('/export', methods=['POST'])
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
        'database': 'connected' if db else 'not_configured',
        'features': {
            'generation': True,
            'history': db is not None,
            'analytics': db is not None
        }
    }
    return jsonify(status), 200

@app.route('/test')
def test():
    return "Flask is working!"

@app.route('/debug/posts')
def debug_posts():
    posts = get_all_temp_posts()
    temp_files = list(TEMP_STORAGE_DIR.glob('*.json'))
    return jsonify({
        'temp_dir': str(TEMP_STORAGE_DIR),
        'temp_dir_exists': TEMP_STORAGE_DIR.exists(),
        'json_files_count': len(temp_files),
        'json_files': [f.name for f in temp_files],
        'posts_loaded': len(posts),
        'posts': posts[:3] if posts else []
    })

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
        
        user_id = session.get('user_id', 'default_user')
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
        
        user_id = session.get('user_id', 'default_user')
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
        user_id = session.get('user_id')
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

@app.route('/history')
def history():
    db = get_supabase_manager()
    if db:
        posts = db.get_recent_posts(50)
    else:
        posts = get_all_temp_posts()
    
    print(f"History route: Found {len(posts) if posts else 0} posts")
    if posts:
        print(f"First post: {posts[0].get('title', 'No title')}")
    
    return render_template('history.html', posts=posts if posts else [])

@app.route('/api/posts/recent')
def api_recent_posts():
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    posts = db.get_recent_posts(20)
    return jsonify({'success': True, 'posts': posts})

@app.route('/api/posts/<post_id>')
def api_get_post(post_id):
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    post = db.get_blog_post_by_id(post_id)
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
def delete_post(post_id):
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    success = db.delete_post(post_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete post'}), 500

@app.route('/analytics')
def analytics():
    db = get_supabase_manager()
    if db:
        blog_analytics = db.get_analytics()
        gen_stats = db.get_generation_stats()
    else:
        blog_analytics = calculate_temp_analytics()
        gen_stats = None
    
    print(f"Analytics route: analytics={blog_analytics is not None}, gen_stats={gen_stats is not None}")
    
    return render_template('analytics.html', analytics=blog_analytics, gen_stats=gen_stats)

@app.route('/api/analytics')
def api_analytics():
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    blog_analytics = db.get_analytics()
    gen_stats = db.get_generation_stats()
    
    return jsonify({
        'success': True,
        'blog_analytics': blog_analytics,
        'generation_stats': gen_stats
    })

@app.route('/api/search')
def search_posts():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    db = get_supabase_manager()
    if not db:
        return jsonify({'error': 'Database not configured'}), 503
    
    results = db.search_posts(query)
    return jsonify({'success': True, 'results': results})

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    server_port = int(os.environ.get('PORT', '8000'))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    print("=" * 60)
    print("REGISTERED ROUTES:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint:30s} {rule.rule:50s} {list(rule.methods)}")
    print("=" * 60)
    print(f"Starting Flask app on port {server_port}")
    print("=" * 60)
    app.run(debug=debug_mode, port=server_port, host='0.0.0.0')
