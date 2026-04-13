import json
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib
from tenant_context import current_tenant_id, normalize_tenant_id

DB_PATH = Path(__file__).parent / 'content_library.db'

def _tenant_id(tenant_id=None):
    return normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'

def _ensure_column(cursor, table, column, definition):
    cursor.execute(f'PRAGMA table_info({table})')
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
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
            tenant_id TEXT,
            post_id TEXT,
            tag TEXT,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
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
            tenant_id TEXT,
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
            tenant_id TEXT,
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            title TEXT NOT NULL,
            content TEXT,
            source_url TEXT,
            source_type TEXT,
            template TEXT,
            tone TEXT,
            model TEXT,
            is_auto_save BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            post_id TEXT,
            version_number INTEGER,
            title TEXT,
            markdown_content TEXT,
            html_content TEXT,
            word_count INTEGER,
            change_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            post_id TEXT,
            scheduled_time TIMESTAMP,
            publish_to TEXT,
            status TEXT DEFAULT 'scheduled',
            published_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')

    for table in ['posts', 'tags', 'analytics', 'templates', 'batch_queue', 'drafts', 'post_versions', 'scheduled_posts']:
        _ensure_column(cursor, table, 'tenant_id', 'TEXT')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_tenant_id ON posts(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_tenant_id ON tags(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_tenant_id ON analytics(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_templates_tenant_id ON templates(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_queue_tenant_id ON batch_queue(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_drafts_tenant_id ON drafts(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_versions_tenant_id ON post_versions(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_scheduled_posts_tenant_id ON scheduled_posts(tenant_id)')
    
    conn.commit()
    conn.close()

def save_post(post_data, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tenant_id = _tenant_id(tenant_id)
    content_hash = hashlib.md5(f'{tenant_id}:{post_data["markdown_content"]}'.encode()).hexdigest()
    
    cursor.execute('''
        INSERT OR REPLACE INTO posts 
        (id, tenant_id, title, content_hash, source_url, source_type, template, tone, model,
         word_count, reading_time, engagement_score, seo_score, viral_potential,
         markdown_content, html_content, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        post_data['id'],
        tenant_id,
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

def get_post(post_id, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM posts WHERE id = ? AND COALESCE(tenant_id, "legacy") = ?', (post_id, _tenant_id(tenant_id)))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_posts(limit=50, offset=0, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM posts 
        WHERE COALESCE(tenant_id, "legacy") = ?
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (_tenant_id(tenant_id), limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def search_posts(query, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM posts 
        WHERE COALESCE(tenant_id, "legacy") = ? AND (title LIKE ? OR markdown_content LIKE ?)
        ORDER BY created_at DESC 
        LIMIT 20
    ''', (_tenant_id(tenant_id), f'%{query}%', f'%{query}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_stats(tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM posts WHERE COALESCE(tenant_id, "legacy") = ?', (_tenant_id(tenant_id),))
    total_posts = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(engagement_score) FROM posts WHERE COALESCE(tenant_id, "legacy") = ?', (_tenant_id(tenant_id),))
    avg_engagement = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT AVG(seo_score) FROM posts WHERE COALESCE(tenant_id, "legacy") = ?', (_tenant_id(tenant_id),))
    avg_seo = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(word_count) FROM posts WHERE COALESCE(tenant_id, "legacy") = ?', (_tenant_id(tenant_id),))
    total_words = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_posts': total_posts,
        'avg_engagement': round(avg_engagement, 1),
        'avg_seo': round(avg_seo, 1),
        'total_words': total_words
    }

def add_to_batch_queue(job_data, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tenant_id = _tenant_id(tenant_id)
    
    cursor.execute('''
        INSERT INTO batch_queue 
        (id, tenant_id, source_url, source_type, template, tone, model, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    ''', (
        job_data['id'],
        tenant_id,
        job_data['source_url'],
        job_data.get('source_type', 'youtube'),
        job_data.get('template', ''),
        job_data.get('tone', ''),
        job_data.get('model', 'gpt-4o')
    ))
    
    conn.commit()
    conn.close()

def get_batch_queue(tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM batch_queue 
        WHERE COALESCE(tenant_id, "legacy") = ?
        ORDER BY created_at DESC
    ''', (_tenant_id(tenant_id),))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_batch_status(job_id, status, progress=None, result_post_id=None, error=None, tenant_id=None):
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
    
    params.extend([job_id, _tenant_id(tenant_id)])
    
    cursor.execute(f'''
        UPDATE batch_queue 
        SET {', '.join(updates)}
        WHERE id = ? AND COALESCE(tenant_id, "legacy") = ?
    ''', params)
    
    conn.commit()
    conn.close()

def save_draft(draft_data, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tenant_id = _tenant_id(tenant_id)
    
    cursor.execute('''
        INSERT OR REPLACE INTO drafts 
        (id, tenant_id, title, content, source_url, source_type, template, tone, model, is_auto_save, updated_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
    ''', (
        draft_data['id'],
        tenant_id,
        draft_data.get('title', 'Untitled Draft'),
        draft_data.get('content', ''),
        draft_data.get('source_url', ''),
        draft_data.get('source_type', ''),
        draft_data.get('template', ''),
        draft_data.get('tone', ''),
        draft_data.get('model', ''),
        draft_data.get('is_auto_save', 0),
        json.dumps(draft_data.get('metadata', {}))
    ))
    
    conn.commit()
    conn.close()
    return draft_data['id']

def get_draft(draft_id, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM drafts WHERE id = ? AND COALESCE(tenant_id, "legacy") = ?', (draft_id, _tenant_id(tenant_id)))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_drafts(limit=50, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM drafts 
        WHERE COALESCE(tenant_id, "legacy") = ?
        ORDER BY updated_at DESC 
        LIMIT ?
    ''', (_tenant_id(tenant_id), limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def delete_draft(draft_id, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drafts WHERE id = ? AND COALESCE(tenant_id, "legacy") = ?', (draft_id, _tenant_id(tenant_id)))
    conn.commit()
    conn.close()

def save_post_version(post_id, version_data, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tenant_id = _tenant_id(tenant_id)
    
    cursor.execute('SELECT COALESCE(MAX(version_number), 0) FROM post_versions WHERE post_id = ? AND COALESCE(tenant_id, "legacy") = ?', (post_id, tenant_id))
    max_version = cursor.fetchone()[0]
    new_version = max_version + 1
    
    cursor.execute('''
        INSERT INTO post_versions 
        (tenant_id, post_id, version_number, title, markdown_content, html_content, word_count, change_description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tenant_id,
        post_id,
        new_version,
        version_data.get('title', ''),
        version_data.get('markdown_content', ''),
        version_data.get('html_content', ''),
        version_data.get('word_count', 0),
        version_data.get('change_description', '')
    ))
    
    conn.commit()
    conn.close()
    return new_version

def get_post_versions(post_id, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM post_versions 
        WHERE post_id = ? AND COALESCE(tenant_id, "legacy") = ?
        ORDER BY version_number DESC
    ''', (post_id, _tenant_id(tenant_id)))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_post_version(post_id, version_number, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM post_versions 
        WHERE post_id = ? AND version_number = ? AND COALESCE(tenant_id, "legacy") = ?
    ''', (post_id, version_number, _tenant_id(tenant_id)))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def schedule_post(schedule_data, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tenant_id = _tenant_id(tenant_id)
    
    cursor.execute('''
        INSERT OR REPLACE INTO scheduled_posts 
        (id, tenant_id, post_id, scheduled_time, publish_to, status)
        VALUES (?, ?, ?, ?, ?, 'scheduled')
    ''', (
        schedule_data['id'],
        tenant_id,
        schedule_data['post_id'],
        schedule_data['scheduled_time'],
        schedule_data.get('publish_to', 'medium')
    ))
    
    conn.commit()
    conn.close()
    return schedule_data['id']

def get_scheduled_posts(status='scheduled', tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if status:
        cursor.execute('''
            SELECT * FROM scheduled_posts 
            WHERE status = ? AND COALESCE(tenant_id, "legacy") = ?
            ORDER BY scheduled_time ASC
        ''', (status, _tenant_id(tenant_id)))
    else:
        cursor.execute('''
            SELECT * FROM scheduled_posts 
            WHERE COALESCE(tenant_id, "legacy") = ?
            ORDER BY scheduled_time DESC
        ''', (_tenant_id(tenant_id),))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_scheduled_post_status(schedule_id, status, error=None, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if status == 'published':
        cursor.execute('''
            UPDATE scheduled_posts 
            SET status = ?, published_at = CURRENT_TIMESTAMP
            WHERE id = ? AND COALESCE(tenant_id, "legacy") = ?
        ''', (status, schedule_id, _tenant_id(tenant_id)))
    else:
        cursor.execute('''
            UPDATE scheduled_posts 
            SET status = ?, error_message = ?
            WHERE id = ? AND COALESCE(tenant_id, "legacy") = ?
        ''', (status, error, schedule_id, _tenant_id(tenant_id)))
    
    conn.commit()
    conn.close()

def delete_scheduled_post(schedule_id, tenant_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scheduled_posts WHERE id = ? AND COALESCE(tenant_id, "legacy") = ?', (schedule_id, _tenant_id(tenant_id)))
    conn.commit()
    conn.close()

init_db()
