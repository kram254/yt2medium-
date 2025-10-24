import os
import base64
import markdown
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
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

print("=" * 60)
print("STARTING FLASK APP")
print("=" * 60)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
load_dotenv()

print(f"Flask app name: {app.name}")
print(f"Flask root path: {app.root_path}")
print(f"Template folder: {app.template_folder}")

ai_manager = None

DEFAULT_MODEL = 'gpt-4o'

def get_ai_manager():
    global ai_manager
    if ai_manager is None:
        print("Initializing AIProviderManager...")
        ai_manager = AIProviderManager()
        print("AIProviderManager initialized successfully")
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

def generate_blog_post_text(user_input, model):
    try:
        input_type = detect_input_type(user_input)
        
        if input_type == 'youtube':
            content_context = get_youtube_transcript(user_input)
        elif input_type == 'url':
            content_context = scrape_web_content(user_input)
        else:
            if any(keyword in user_input.lower() for keyword in ['trending', 'latest', 'today', 'recent', 'current']):
                content_context = research_trending_topic(user_input, get_ai_manager())
            else:
                content_context = f"User Request: {user_input}\n\nCreate comprehensive, well-researched content based on this topic or prompt."
        
        prompt = prompts.get_blog_gen_prompt()
        response = get_ai_manager().generate_content(prompt, content_context)
        return clean_markdown(response)
    except Exception as e:
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
        return clean_markdown(response)
    except Exception as e:
        print(f"Enhancement error: {e}")
        return blog_text

@app.route('/generate', methods=['POST'])
def generate_blog():
    print("Generate blog route called!")
    try:
        data = request.get_json()
        user_input = data.get('youtube_link', '').strip()
        model = data.get('model', DEFAULT_MODEL)
        enhance = data.get('enhance', False)
        print(f"User input: {user_input[:100] if user_input else 'None'}")
        
        if not user_input:
            return jsonify({'error': 'Input is required'}), 400
        
        blog_post_text = generate_blog_post_text(user_input, model)
        
        if enhance:
            blog_post_text = enhance_blog_post(blog_post_text)
        
        title = extract_title_from_markdown(blog_post_text)
        
        images = generate_images_for_blog(title, blog_post_text)
        
        reading_time = estimate_reading_time(blog_post_text)
        key_quotes = extract_key_quotes(blog_post_text)
        engagement_score = calculate_engagement_score(blog_post_text)
        
        blog_post_with_mermaid = convert_mermaid_to_html(blog_post_text)
        blog_post_html = markdown.markdown(
            blog_post_with_mermaid, 
            extensions=["tables", "fenced_code", "nl2br", "codehilite"]
        )
        
        return jsonify({
            'success': True,
            'title': title,
            'blog_post_html': blog_post_html,
            'blog_post_markdown': blog_post_text,
            'image_data': images[0],
            'image_data_2': images[1],
            'reading_time': reading_time,
            'key_quotes': key_quotes,
            'engagement_score': engagement_score,
            'word_count': len(blog_post_text.split())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/blog', methods=['GET', 'POST'])
def blog_post():
    print(f"Blog post route called! Method: {request.method}")
    if request.method == 'POST':
        user_input = request.form.get('youtube_link', '').strip()
        model = request.form.get('model', DEFAULT_MODEL)
        enhance = request.form.get('enhance') == 'on'
        print(f"Form input: {user_input[:100] if user_input else 'None'}")
        
        if not user_input:
            return render_template('index.html', error='Please enter a URL or topic')
        
        try:
            blog_post_text = generate_blog_post_text(user_input, model)
            
            if enhance:
                blog_post_text = enhance_blog_post(blog_post_text)
            
            title = extract_title_from_markdown(blog_post_text)
            images = generate_images_for_blog(title, blog_post_text)
            reading_time = estimate_reading_time(blog_post_text)
            key_quotes = extract_key_quotes(blog_post_text)
            engagement_score = calculate_engagement_score(blog_post_text)
            
            blog_post_with_mermaid = convert_mermaid_to_html(blog_post_text)
            blog_post_html = markdown.markdown(
                blog_post_with_mermaid,
                extensions=["tables", "fenced_code", "nl2br", "codehilite"]
            )
            
            return render_template(
                'blog-post.html',
                title=title,
                blog_post_html=blog_post_html,
                blog_post_markdown=blog_post_text,
                image_data=images[0],
                image_data_2=images[1],
                reading_time=reading_time,
                key_quotes=key_quotes,
                engagement_score=engagement_score,
                word_count=len(blog_post_text.split())
            )
        except Exception as e:
            return render_template('index.html', error=f'Error generating blog post: {str(e)}')
    
    return redirect(url_for('index'))

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
    return jsonify({'status': 'healthy'}), 200

@app.route('/test')
def test():
    return "Flask is working!"

if __name__ == '__main__':
    server_port = int(os.environ.get('PORT', '5000'))
    print("=" * 60)
    print("REGISTERED ROUTES:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint:30s} {rule.rule:50s} {list(rule.methods)}")
    print("=" * 60)
    print(f"Starting Flask app on port {server_port}")
    print("=" * 60)
    app.run(debug=True, port=server_port, host='0.0.0.0')
