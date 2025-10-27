import os
import re
import google.auth
from urllib.parse import urlparse, parse_qs

def get_project_id():
    project_id = os.getenv('PROJECT_ID')
    if project_id:
        return project_id
    try:
        _, project_id = google.auth.default()
        if project_id:
            return project_id
    except google.auth.exceptions.DefaultCredentialsError:
        pass
    raise ValueError(
        "Could not determine the project ID. "
        "Please set the PROJECT_ID environment variable in a .env file for "
        "local development, or ensure the application is running in a "
        "Google Cloud environment."
    )

def extract_video_id(url):
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]
    elif 'youtube.com' in url:
        parsed_url = urlparse(url)
        if 'v' in parse_qs(parsed_url.query):
            return parse_qs(parsed_url.query)['v'][0]
    return None

def extract_title_from_markdown(markdown_text):
    default_title = "Your AI-Generated Medium Post"
    lines = markdown_text.split('\n')
    for line in lines:
        if line.startswith('## '):
            title = line.strip('# ').strip()
            if len(title) > 5:
                return title
    return default_title

def estimate_reading_time(text):
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"

def extract_key_quotes(markdown_text):
    quotes = []
    for line in markdown_text.split('\n'):
        if line.startswith('>'):
            quote = line.strip('> ').strip()
            if len(quote) > 20:
                quotes.append(quote)
    return quotes[:3]

def validate_youtube_url(url):
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+',
    ]
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    return False

def validate_input(user_input):
    if not user_input or len(user_input.strip()) < 3:
        return False
    return True

def clean_markdown(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text

def convert_mermaid_to_html(markdown_text):
    pattern = r'```mermaid\n(.*?)```'
    
    def replace_mermaid(match):
        mermaid_code = match.group(1)
        return f'<div class="mermaid">\n{mermaid_code}\n</div>'
    
    result = re.sub(pattern, replace_mermaid, markdown_text, flags=re.DOTALL)
    return result

def calculate_engagement_score(text):
    score = 0
    paragraphs = text.split('\n\n')
    if len(paragraphs) >= 8:
        score += 10
    short_paragraphs = sum(1 for p in paragraphs if len(p.split()) < 50)
    score += min(20, short_paragraphs * 2)
    bold_count = text.count('**')
    score += min(15, bold_count)
    questions = text.count('?')
    score += min(15, questions * 2)
    words = len(text.split())
    if 1000 <= words <= 1500:
        score += 25
    elif 800 <= words <= 2400:
        score += 20
    elif 600 <= words <= 3000:
        score += 15
    else:
        score += 5
    subheadings = text.count('##')
    if 4 <= subheadings <= 7:
        score += 15
    else:
        score += 5
    quotes = text.count('>')
    score += min(10, quotes * 3)
    return min(100, score)
