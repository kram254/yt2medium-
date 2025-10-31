import re
import json

def export_to_medium(markdown_content, title):
    medium_formatted = markdown_content
    
    medium_formatted = re.sub(r'```mermaid\n.*?```', '', medium_formatted, flags=re.DOTALL)
    
    return {
        'title': title,
        'content': medium_formatted,
        'contentFormat': 'markdown',
        'publishStatus': 'draft'
    }

def export_to_devto(markdown_content, title, tags=None):
    if tags is None:
        tags = ['programming', 'tutorial', 'webdev']
    
    front_matter = f"""---
title: {title}
published: false
tags: {', '.join(tags[:4])}
---

"""
    
    devto_content = markdown_content
    devto_content = re.sub(r'```mermaid\n.*?```', '', devto_content, flags=re.DOTALL)
    
    return front_matter + devto_content

def export_to_hashnode(markdown_content, title, tags=None):
    if tags is None:
        tags = ['programming', 'tutorial', 'technology']
    
    hashnode_formatted = markdown_content
    hashnode_formatted = re.sub(r'```mermaid\n.*?```', '', hashnode_formatted, flags=re.DOTALL)
    
    return {
        'title': title,
        'contentMarkdown': hashnode_formatted,
        'tags': [{'name': tag} for tag in tags[:5]],
        'isPartOfPublication': {'publicationId': 'YOUR_PUBLICATION_ID'}
    }

def export_to_linkedin(markdown_content, title):
    linkedin_content = f"{title}\n\n"
    
    linkedin_content += re.sub(r'```.*?```', '[Code snippet - see full article]', markdown_content, flags=re.DOTALL)
    linkedin_content = re.sub(r'!\[.*?\]\(.*?\)', '[Image]', linkedin_content)
    linkedin_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', linkedin_content)
    linkedin_content = re.sub(r'#{1,6}\s', '', linkedin_content)
    linkedin_content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', linkedin_content)
    
    if len(linkedin_content) > 3000:
        linkedin_content = linkedin_content[:2950] + '...\n\n[Read full article]'
    
    return linkedin_content

def export_to_substack(markdown_content, title):
    substack_html = markdown_to_html_simple(markdown_content)
    
    return {
        'title': title,
        'body': substack_html,
        'type': 'newsletter'
    }

def export_to_ghost(markdown_content, title, tags=None):
    if tags is None:
        tags = ['technology', 'programming']
    
    ghost_formatted = markdown_content
    ghost_formatted = re.sub(r'```mermaid\n.*?```', '', ghost_formatted, flags=re.DOTALL)
    
    return {
        'posts': [{
            'title': title,
            'markdown': ghost_formatted,
            'status': 'draft',
            'tags': [{'name': tag} for tag in tags]
        }]
    }

def export_to_wordpress(markdown_content, title):
    wp_html = markdown_to_html_simple(markdown_content)
    
    return {
        'title': title,
        'content': wp_html,
        'status': 'draft',
        'format': 'standard'
    }

def markdown_to_html_simple(markdown_text):
    html = markdown_text
    
    html = re.sub(r'#{1}\s(.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'#{2}\s(.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'#{3}\s(.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    html = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', html)
    
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    html = re.sub(r'```(.*?)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    
    html = re.sub(r'^\* (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
    
    html = re.sub(r'^([^<\n].+)$', r'<p>\1</p>', html, flags=re.MULTILINE)
    
    return html

def create_twitter_thread(markdown_content, title, max_tweets=10):
    paragraphs = [p.strip() for p in markdown_content.split('\n\n') if p.strip()]
    
    tweets = [f"🧵 {title}\n\n1/"]
    current_tweet = ""
    tweet_num = 2
    
    for para in paragraphs:
        para_clean = re.sub(r'#{1,6}\s', '', para)
        para_clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', para_clean)
        para_clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', para_clean)
        para_clean = re.sub(r'```.*?```', '[code snippet]', para_clean, flags=re.DOTALL)
        
        if len(para_clean) > 250:
            para_clean = para_clean[:247] + '...'
        
        if len(current_tweet) + len(para_clean) + 10 < 280:
            current_tweet += para_clean + "\n\n"
        else:
            if current_tweet:
                tweets.append(f"{current_tweet.strip()}\n\n{tweet_num}/")
                tweet_num += 1
            current_tweet = para_clean + "\n\n"
        
        if len(tweets) >= max_tweets:
            break
    
    if current_tweet and len(tweets) < max_tweets:
        tweets.append(f"{current_tweet.strip()}\n\n{tweet_num}/")
    
    return tweets

def export_to_json(post_data):
    return json.dumps(post_data, indent=2)

def export_to_txt(markdown_content, title):
    txt_content = f"{title}\n{'=' * len(title)}\n\n"
    
    txt_clean = re.sub(r'#{1,6}\s', '', markdown_content)
    txt_clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', txt_clean)
    txt_clean = re.sub(r'\*([^\*]+)\*', r'\1', txt_clean)
    txt_clean = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\1 (\2)', txt_clean)
    txt_clean = re.sub(r'```.*?```', '[code block]', txt_clean, flags=re.DOTALL)
    
    txt_content += txt_clean
    return txt_content

def export_to_notion(markdown_content, title):
    notion_blocks = []
    
    notion_blocks.append({
        'object': 'block',
        'type': 'heading_1',
        'heading_1': {
            'rich_text': [{'type': 'text', 'text': {'content': title}}]
        }
    })
    
    paragraphs = markdown_content.split('\n\n')
    for para in paragraphs:
        if para.strip().startswith('#'):
            level = len(para.split()[0])
            text = para.lstrip('#').strip()
            notion_blocks.append({
                'object': 'block',
                'type': f'heading_{min(level, 3)}',
                f'heading_{min(level, 3)}': {
                    'rich_text': [{'type': 'text', 'text': {'content': text}}]
                }
            })
        elif para.strip():
            notion_blocks.append({
                'object': 'block',
                'type': 'paragraph',
                'paragraph': {
                    'rich_text': [{'type': 'text', 'text': {'content': para.strip()}}]
                }
            })
    
    return {'blocks': notion_blocks}

def export_to_email_html(markdown_content, title):
    email_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a1a1a; font-size: 28px; margin-bottom: 20px; }}
            h2 {{ color: #2a2a2a; font-size: 22px; margin-top: 30px; margin-bottom: 15px; }}
            h3 {{ color: #3a3a3a; font-size: 18px; margin-top: 20px; margin-bottom: 10px; }}
            p {{ margin-bottom: 15px; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            strong {{ font-weight: 600; }}
            code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
            pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            ul, ol {{ margin-bottom: 15px; padding-left: 30px; }}
            li {{ margin-bottom: 8px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        {markdown_to_html_simple(markdown_content)}
    </body>
    </html>
    """
    return email_html

def get_export_formats():
    return {
        'medium': 'Medium (JSON)',
        'devto': 'Dev.to (Markdown with front matter)',
        'hashnode': 'Hashnode (JSON)',
        'linkedin': 'LinkedIn (Plain text)',
        'substack': 'Substack (HTML)',
        'ghost': 'Ghost (JSON)',
        'wordpress': 'WordPress (HTML)',
        'twitter': 'Twitter Thread',
        'json': 'JSON (Full data)',
        'txt': 'Plain Text',
        'notion': 'Notion (Blocks)',
        'email': 'Email (HTML)'
    }
