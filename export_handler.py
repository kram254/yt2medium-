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

def get_export_formats():
    return {
        'medium': 'Medium (JSON)',
        'devto': 'Dev.to (Markdown with front matter)',
        'hashnode': 'Hashnode (JSON)',
        'linkedin': 'LinkedIn (Plain text)',
        'substack': 'Substack (HTML)',
        'ghost': 'Ghost (JSON)',
        'wordpress': 'WordPress (HTML)',
        'twitter': 'Twitter Thread'
    }
