"""
PostgreSQL database client — replaces Supabase for data persistence.

Provides the same interface as SupabaseManager's data methods
(save_blog_post, get_blog_post_by_id, get_recent_posts, etc.)
using direct PostgreSQL connections via psycopg2.

Auth remains handled by Supabase Auth (supabase_client.py).
"""

import os
import json
import uuid
import psycopg2
import psycopg2.extras
from datetime import datetime
from contextlib import contextmanager
from tenant_context import current_tenant_id, normalize_tenant_id

# ── Connection pool ──────────────────────────────────────────

_pool = None


def _get_database_url():
    """Get the PostgreSQL connection string from environment."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Build from individual components as fallback
        host = os.environ.get("PGHOST", "localhost")
        port = os.environ.get("PGPORT", "5432")
        dbname = os.environ.get("PGDATABASE", "yt2medium")
        user = os.environ.get("PGUSER", "postgres")
        password = os.environ.get("PGPASSWORD", "")
        url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return url


def _get_pool():
    """Get or create the connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        from psycopg2 import pool
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=_get_database_url()
        )
    return _pool


@contextmanager
def get_connection():
    """Get a connection from the pool with auto-commit and return."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ── Schema initialization ───────────────────────────────────

def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    user_id TEXT,
                    tenant_id TEXT DEFAULT 'legacy',
                    title TEXT NOT NULL,
                    markdown_content TEXT NOT NULL,
                    html_content TEXT NOT NULL,
                    image_header TEXT,
                    image_content TEXT,
                    reading_time INTEGER,
                    word_count INTEGER,
                    engagement_score INTEGER,
                    seo_score INTEGER,
                    viral_potential INTEGER,
                    readability_score INTEGER,
                    key_quotes JSONB DEFAULT '[]'::jsonb,
                    seo_recommendations JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS generation_logs (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    user_id TEXT,
                    tenant_id TEXT DEFAULT 'legacy',
                    user_input TEXT NOT NULL,
                    input_type TEXT,
                    model_used TEXT,
                    template TEXT,
                    tone TEXT,
                    enhanced BOOLEAN DEFAULT FALSE,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    generation_time NUMERIC,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_blog_posts_user_tenant
                    ON blog_posts(user_id, tenant_id);
                CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at
                    ON blog_posts(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_generation_logs_user_tenant
                    ON generation_logs(user_id, tenant_id);
                CREATE INDEX IF NOT EXISTS idx_generation_logs_created_at
                    ON generation_logs(created_at DESC);

                CREATE TABLE IF NOT EXISTS users (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    google_sub TEXT UNIQUE,
                    name TEXT,
                    avatar_url TEXT,
                    session_token_hash TEXT,
                    refresh_token_hash TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login_at TIMESTAMP WITH TIME ZONE
                );

                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_session_token ON users(session_token_hash);

                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';

                DROP TRIGGER IF EXISTS update_blog_posts_updated_at ON blog_posts;
                CREATE TRIGGER update_blog_posts_updated_at
                    BEFORE UPDATE ON blog_posts
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
    print("PostgreSQL: tables initialized")


# ── PostgresManager (drop-in replacement for SupabaseManager data methods) ──

class PostgresManager:
    """
    Provides the same data-access interface as SupabaseManager
    so app.py can swap `db = get_supabase_manager()` for `db = get_db_manager()`
    with zero changes to call sites.
    """

    def _resolve_tenant(self, tenant_id):
        return normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'

    def _row_to_dict(self, cursor):
        """Convert a cursor row to a dict using column names."""
        if cursor.description is None:
            return None
        columns = [col.name for col in cursor.description]
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(zip(columns, row))

    def _rows_to_dicts(self, cursor):
        """Convert all cursor rows to a list of dicts."""
        if cursor.description is None:
            return []
        columns = [col.name for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _serialize_row(self, row):
        """Ensure JSON-safe types for API responses."""
        if not row:
            return row
        for key, val in row.items():
            if isinstance(val, datetime):
                row[key] = val.isoformat()
            elif isinstance(val, uuid.UUID):
                row[key] = str(val)
        return row

    # ── Blog posts ───────────────────────────────────────────

    def save_blog_post(self, blog_data, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            post_id = str(uuid.uuid4())
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO blog_posts
                            (id, user_id, tenant_id, title, markdown_content, html_content,
                             image_header, image_content, reading_time, word_count,
                             engagement_score, seo_score, viral_potential, readability_score,
                             key_quotes, seo_recommendations, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING *
                    """, (
                        post_id,
                        user_id,
                        tenant_id,
                        blog_data.get('title'),
                        blog_data.get('markdown_content') or blog_data.get('blog_post_markdown'),
                        blog_data.get('html_content') or blog_data.get('blog_post_html'),
                        blog_data.get('image_header') or blog_data.get('image_data'),
                        blog_data.get('image_content') or blog_data.get('image_data_2'),
                        blog_data.get('reading_time'),
                        blog_data.get('word_count'),
                        blog_data.get('engagement_score'),
                        blog_data.get('seo_score'),
                        blog_data.get('viral_potential'),
                        blog_data.get('readability_score'),
                        json.dumps(blog_data.get('key_quotes', [])),
                        json.dumps(blog_data.get('seo_recommendations', [])),
                        datetime.utcnow().isoformat()
                    ))
                    result = self._row_to_dict(cur)
                    return self._serialize_row(result)
        except Exception as e:
            print(f"Error saving blog post: {e}")
            return None

    def get_blog_post_by_id(self, post_id, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        # Try user-owned first
                        cur.execute(
                            "SELECT * FROM blog_posts WHERE id = %s AND user_id = %s AND tenant_id = %s",
                            (post_id, user_id, tenant_id)
                        )
                        row = self._row_to_dict(cur)
                        if not row:
                            # Try legacy (no user_id)
                            cur.execute(
                                "SELECT * FROM blog_posts WHERE id = %s AND user_id IS NULL AND tenant_id = %s",
                                (post_id, tenant_id)
                            )
                            row = self._row_to_dict(cur)
                    else:
                        cur.execute(
                            "SELECT * FROM blog_posts WHERE id = %s AND tenant_id = %s",
                            (post_id, tenant_id)
                        )
                        row = self._row_to_dict(cur)

                    if row:
                        # Parse JSON fields
                        for field in ('key_quotes', 'seo_recommendations'):
                            raw = row.get(field)
                            if isinstance(raw, str):
                                row[field] = json.loads(raw)
                            elif raw is None:
                                row[field] = []
                        return self._serialize_row(row)
                    return None
        except Exception as e:
            print(f"Error retrieving blog post: {e}")
            return None

    def get_recent_posts(self, user_id=None, tenant_id=None, limit=20):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute("""
                            SELECT id, title, created_at, word_count, engagement_score,
                                   seo_score, viral_potential
                            FROM blog_posts
                            WHERE (user_id = %s OR user_id IS NULL) AND tenant_id = %s
                            ORDER BY created_at DESC
                            LIMIT %s
                        """, (user_id, tenant_id, limit))
                    else:
                        cur.execute("""
                            SELECT id, title, created_at, word_count, engagement_score,
                                   seo_score, viral_potential
                            FROM blog_posts
                            WHERE tenant_id = %s
                            ORDER BY created_at DESC
                            LIMIT %s
                        """, (tenant_id, limit))
                    rows = self._rows_to_dicts(cur)
                    return [self._serialize_row(r) for r in rows]
        except Exception as e:
            print(f"Error retrieving recent posts: {e}")
            return []

    def search_posts(self, query_str, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    params = [f"%{query_str}%", tenant_id]
                    sql = """
                        SELECT id, title, created_at, word_count, engagement_score
                        FROM blog_posts
                        WHERE title ILIKE %s AND tenant_id = %s
                    """
                    if user_id:
                        sql += " AND user_id = %s"
                        params.append(user_id)
                    sql += " ORDER BY created_at DESC LIMIT 20"
                    cur.execute(sql, params)
                    rows = self._rows_to_dicts(cur)
                    return [self._serialize_row(r) for r in rows]
        except Exception as e:
            print(f"Error searching posts: {e}")
            return []

    def get_drafts_count(self, user_id, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM blog_posts WHERE user_id = %s AND tenant_id = %s",
                        (user_id, tenant_id)
                    )
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting drafts count: {e}")
            return 0

    def delete_post(self, post_id, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute(
                            "DELETE FROM blog_posts WHERE id = %s AND (user_id = %s OR user_id IS NULL) AND tenant_id = %s",
                            (post_id, user_id, tenant_id)
                        )
                    else:
                        cur.execute(
                            "DELETE FROM blog_posts WHERE id = %s AND tenant_id = %s",
                            (post_id, tenant_id)
                        )
                    return True
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False

    def get_analytics(self, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute(
                            "SELECT * FROM blog_posts WHERE (user_id = %s OR user_id IS NULL) AND tenant_id = %s",
                            (user_id, tenant_id)
                        )
                    else:
                        cur.execute(
                            "SELECT * FROM blog_posts WHERE tenant_id = %s",
                            (tenant_id,)
                        )
                    posts = self._rows_to_dicts(cur)

            if not posts:
                return {
                    'total_posts': 0,
                    'avg_engagement_score': 0,
                    'avg_seo_score': 0,
                    'avg_viral_potential': 0,
                    'total_words_written': 0,
                    'recent_posts': []
                }

            total = len(posts)
            avg_engagement = sum(p.get('engagement_score') or 0 for p in posts) / total
            avg_seo = sum(p.get('seo_score') or 0 for p in posts) / total
            avg_viral = sum(p.get('viral_potential') or 0 for p in posts) / total
            total_words = sum(p.get('word_count') or 0 for p in posts)

            recent = sorted(posts, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
            return {
                'total_posts': total,
                'avg_engagement_score': round(avg_engagement, 1),
                'avg_seo_score': round(avg_seo, 1),
                'avg_viral_potential': round(avg_viral, 1),
                'total_words_written': total_words,
                'recent_posts': [self._serialize_row(r) for r in recent]
            }
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return None

    def update_post(self, post_id, updates, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            if not updates:
                return None

            set_clauses = []
            params = []
            for key, val in updates.items():
                set_clauses.append(f"{key} = %s")
                params.append(val)

            params.extend([post_id, tenant_id])
            where = "id = %s AND tenant_id = %s"
            if user_id:
                where += " AND user_id = %s"
                params.append(user_id)

            sql = f"UPDATE blog_posts SET {', '.join(set_clauses)} WHERE {where} RETURNING *"

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    row = self._row_to_dict(cur)
                    return self._serialize_row(row)
        except Exception as e:
            print(f"Error updating post: {e}")
            return None

    # ── Generation logs ──────────────────────────────────────

    def save_generation_log(self, log_data, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO generation_logs
                            (user_id, tenant_id, user_input, input_type, model_used,
                             template, tone, enhanced, success, error_message,
                             generation_time, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING *
                    """, (
                        user_id,
                        tenant_id,
                        log_data.get('user_input'),
                        log_data.get('input_type'),
                        log_data.get('model'),
                        log_data.get('template'),
                        log_data.get('tone'),
                        log_data.get('enhanced', False),
                        log_data.get('success', True),
                        log_data.get('error'),
                        log_data.get('generation_time'),
                        datetime.utcnow().isoformat()
                    ))
                    row = self._row_to_dict(cur)
                    return self._serialize_row(row)
        except Exception as e:
            print(f"Error saving generation log: {e}")
            return None

    def get_generation_stats(self, user_id=None, tenant_id=None):
        try:
            tenant_id = self._resolve_tenant(tenant_id)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    sql = "SELECT * FROM generation_logs WHERE tenant_id = %s"
                    params = [tenant_id]
                    if user_id:
                        sql += " AND user_id = %s"
                        params.append(user_id)
                    cur.execute(sql, params)
                    logs = self._rows_to_dicts(cur)

            if not logs:
                return None

            total = len(logs)
            successful = sum(1 for l in logs if l.get('success', True))

            templates_used = {}
            models_used = {}
            for log in logs:
                template = log.get('template') or 'default'
                templates_used[template] = templates_used.get(template, 0) + 1
                model = log.get('model_used') or 'unknown'
                models_used[model] = models_used.get(model, 0) + 1

            top_model = max(models_used, key=models_used.get) if models_used else None

            return {
                'total_generations': total,
                'successful_generations': successful,
                'failed_generations': total - successful,
                'success_rate': round((successful / total * 100), 1) if total > 0 else 0,
                'templates_used': templates_used,
                'models_used': models_used,
                'top_model': top_model,
            }
        except Exception as e:
            print(f"Error getting generation stats: {e}")
            return None


# ── Singleton ────────────────────────────────────────────────

_manager = None


def get_db_manager():
    """
    Get the PostgresManager singleton. Returns None if DATABASE_URL
    is not configured (graceful fallback, same as get_supabase_manager).
    """
    global _manager
    if _manager is not None:
        return _manager
    try:
        db_url = _get_database_url()
        if not db_url or db_url == "postgresql://postgres:@localhost:5432/yt2medium":
            # No real DB configured — check if env vars are set
            if not os.environ.get("DATABASE_URL") and not os.environ.get("PGHOST"):
                print("Warning: PostgreSQL not configured (set DATABASE_URL)")
                return None
        _manager = PostgresManager()
        init_db()
        return _manager
    except Exception as e:
        print(f"Warning: PostgreSQL not available: {e}")
        return None
