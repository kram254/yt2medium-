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
    calculate_engagement_score
)
from ai_providers import AIProviderManager, get_youtube_transcript

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
load_dotenv()

ai_manager = AIProviderManager()

DEFAULT_MODEL = 'gpt-4o'

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def generate_image(blog_title):
    try:
        prompt = prompts.get_image_gen_prompt(blog_title)
        return ai_manager.generate_image(prompt)
    except Exception as e:
        print(f"Image generation error: {e}")
        return None

def generate_blog_post_text(youtube_link, model):
    try:
        video_context = get_youtube_transcript(youtube_link)
        prompt = prompts.get_blog_gen_prompt()
        response = ai_manager.generate_content(prompt, video_context)
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
        response = ai_manager.generate_content(enhancement_prompt)
        return clean_markdown(response)
    except Exception as e:
        print(f"Enhancement error: {e}")
        return blog_text

@app.route('/generate', methods=['POST'])
def generate_blog():
    try:
        data = request.get_json()
        youtube_link = data.get('youtube_link', '').strip()
        model = data.get('model', DEFAULT_MODEL)
        enhance = data.get('enhance', False)
        
        if not youtube_link:
            return jsonify({'error': 'YouTube link is required'}), 400
        
        if not validate_youtube_url(youtube_link):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        blog_post_text = generate_blog_post_text(youtube_link, model)
        
        if enhance:
            blog_post_text = enhance_blog_post(blog_post_text)
        
        title = extract_title_from_markdown(blog_post_text)
        
        image_data = generate_image(title)
        
        reading_time = estimate_reading_time(blog_post_text)
        key_quotes = extract_key_quotes(blog_post_text)
        engagement_score = calculate_engagement_score(blog_post_text)
        
        blog_post_html = markdown.markdown(
            blog_post_text, 
            extensions=["tables", "fenced_code", "nl2br"]
        )
        
        return jsonify({
            'success': True,
            'title': title,
            'blog_post_html': blog_post_html,
            'blog_post_markdown': blog_post_text,
            'image_data': image_data,
            'reading_time': reading_time,
            'key_quotes': key_quotes,
            'engagement_score': engagement_score,
            'word_count': len(blog_post_text.split())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/blog', methods=['GET', 'POST'])
def blog_post():
    if request.method == 'POST':
        youtube_link = request.form.get('youtube_link', '').strip()
        model = request.form.get('model', DEFAULT_MODEL)
        enhance = request.form.get('enhance') == 'on'
        
        if not youtube_link or not validate_youtube_url(youtube_link):
            return render_template('index.html', error='Please enter a valid YouTube URL')
        
        try:
            blog_post_text = generate_blog_post_text(youtube_link, model)
            
            if enhance:
                blog_post_text = enhance_blog_post(blog_post_text)
            
            title = extract_title_from_markdown(blog_post_text)
            image_data = generate_image(title)
            reading_time = estimate_reading_time(blog_post_text)
            key_quotes = extract_key_quotes(blog_post_text)
            engagement_score = calculate_engagement_score(blog_post_text)
            
            blog_post_html = markdown.markdown(
                blog_post_text,
                extensions=["tables", "fenced_code", "nl2br"]
            )
            
            return render_template(
                'blog-post.html',
                title=title,
                blog_post_html=blog_post_html,
                blog_post_markdown=blog_post_text,
                image_data=image_data,
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

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=True, port=server_port, host='0.0.0.0')
