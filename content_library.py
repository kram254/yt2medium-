import json
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

DB_PATH = Path(__file__).parent / 'content_library.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content_hash TEXT UNIQUE,
            source_url TEXT,
            source_type TEXT,
            template TEXT,
            tone TEXT,
            model TEXT,
            word_count INTEGER,
            reading_time INTEGER,
            engagement_score INTEGER,
            seo_score INTEGER,
            viral_potential INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published BOOLEAN DEFAULT 0,
            views INTEGER DEFAULT 0,
            markdown_content TEXT,
            html_content TEXT,
            metadata TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT,
            tag TEXT,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT,
            date DATE,
            views INTEGER DEFAULT 0,
            reads INTEGER DEFAULT 0,
            claps INTEGER DEFAULT 0,
            highlights INTEGER DEFAULT 0,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            prompt_template TEXT,
            tone TEXT,
            style_guide TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_queue (
            id TEXT PRIMARY KEY,
            source_url TEXT,
            source_type TEXT,
            template TEXT,
            tone TEXT,
            model TEXT,
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            result_post_id TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_post(post_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    content_hash = hashlib.md5(post_data['markdown_content'].encode()).hexdigest()
    
    cursor.execute('''
        INSERT OR REPLACE INTO posts 
        (id, title, content_hash, source_url, source_type, template, tone, model,
         word_count, reading_time, engagement_score, seo_score, viral_potential,
         markdown_content, html_content, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        post_data['id'],
        post_data['title'],
        content_hash,
        post_data.get('source_url', ''),
        post_data.get('source_type', 'youtube'),
        post_data.get('template', ''),
        post_data.get('tone', ''),
        post_data.get('model', ''),
        post_data.get('word_count', 0),
        post_data.get('reading_time', 0),
        post_data.get('engagement_score', 0),
        post_data.get('seo_score', 0),
        post_data.get('viral_potential', 0),
        post_data['markdown_content'],
        post_data['html_content'],
        json.dumps(post_data.get('metadata', {}))
    ))
    
    conn.commit()
    conn.close()
    return post_data['id']

def get_post(post_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_posts(limit=50, offset=0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM posts 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def search_posts(query):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM posts 
        WHERE title LIKE ? OR markdown_content LIKE ?
        ORDER BY created_at DESC 
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM posts')
    total_posts = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(engagement_score) FROM posts')
    avg_engagement = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT AVG(seo_score) FROM posts')
    avg_seo = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(word_count) FROM posts')
    total_words = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_posts': total_posts,
        'avg_engagement': round(avg_engagement, 1),
        'avg_seo': round(avg_seo, 1),
        'total_words': total_words
    }

def add_to_batch_queue(job_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO batch_queue 
        (id, source_url, source_type, template, tone, model, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    ''', (
        job_data['id'],
        job_data['source_url'],
        job_data.get('source_type', 'youtube'),
        job_data.get('template', ''),
        job_data.get('tone', ''),
        job_data.get('model', 'gpt-4o')
    ))
    
    conn.commit()
    conn.close()

def get_batch_queue():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM batch_queue 
        ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_batch_status(job_id, status, progress=None, result_post_id=None, error=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = ['status = ?']
    params = [status]
    
    if progress is not None:
        updates.append('progress = ?')
        params.append(progress)
    
    if result_post_id:
        updates.append('result_post_id = ?')
        params.append(result_post_id)
    
    if error:
        updates.append('error_message = ?')
        params.append(error)
    
    if status == 'processing':
        updates.append('started_at = CURRENT_TIMESTAMP')
    elif status in ['completed', 'failed']:
        updates.append('completed_at = CURRENT_TIMESTAMP')
    
    params.append(job_id)
    
    cursor.execute(f'''
        UPDATE batch_queue 
        SET {', '.join(updates)}
        WHERE id = ?
    ''', params)
    
    conn.commit()
    conn.close()

init_db()
