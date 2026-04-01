import os
from supabase import create_client, Client
from flask import session
from datetime import datetime
import json

class SupabaseAuthStorage:
    def __init__(self):
        pass
        
    def get_item(self, key: str) -> str | None:
        # Check both with and without 'sb-' prefix to be safe
        val = session.get(key) or session.get(f"sb-{key}")
        if not val:
            print(f"SupabaseAuthStorage: get_item('{key}') -> NOT FOUND. Session keys: {list(session.keys())}")
        else:
            print(f"SupabaseAuthStorage: get_item('{key}') -> FOUND")
        return val
        
    def set_item(self, key: str, value: str) -> None:
        print(f"SupabaseAuthStorage: set_item('{key}', '[VALUE]')")
        # Store with the exact key Supabase asks for
        session[key] = value
        session.modified = True
        
    def remove_item(self, key: str) -> None:
        print(f"SupabaseAuthStorage: remove_item('{key}')")
        session.pop(key, None)
        session.pop(f"sb-{key}", None)
        session.modified = True

class SupabaseManager:
    def __init__(self):
        self._url = os.environ.get("SUPABASE_URL")
        anon_key = os.environ.get("SUPABASE_KEY")
        service_key = os.environ.get("SUPABASE_SERVICE_KEY")

        if not self._url or not anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

        # Use service role key for database if available, BUT use anon key for auth.
        # Supabase OAuth/PKCE generally expects the anon/client key.
        self._key = service_key or anon_key
        self._anon_key = anon_key
        self._using_service_role = bool(service_key)
        
        from supabase import ClientOptions
        
        # Initialize client with session-based storage for PKCE persistence
        # We use the anon_key for the auth client specifically
        self.client: Client = create_client(
            self._url, 
            self._anon_key if not self._using_service_role else self._anon_key, # Always use anon for auth-related client if possible
            options=ClientOptions(
                flow_type="pkce",
                storage=SupabaseAuthStorage()
            )
        )
        
        # If we have a service role key, we'll create a separate internal client for DB operations
        self._db_client = self.client
        if self._using_service_role:
            self._db_client = create_client(self._url, service_key)
            print("Supabase: initialized with service role for DB and anon key for Auth")
        else:
            print("Supabase: using anon key for both Auth and DB")

    # ── Auth Methods ──────────────────────────────────────────────────

    def sign_up(self, email, password, redirect_url=None):
        try:
            options = {}
            if redirect_url:
                options['email_redirect_to'] = redirect_url
            return self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": options
            })
        except Exception as e:
            print(f"Supabase sign_up error: {e}")
            return None

    def sign_in(self, email, password):
        try:
            return self.client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e:
            print(f"Supabase sign_in error: {e}")
            return None

    def sign_in_with_google(self, redirect_url=None):
        """Return the OAuth URL for Google sign-in."""
        try:
            opts = {}
            if redirect_url:
                opts['redirect_to'] = redirect_url
            return self.client.auth.sign_in_with_oauth({
                "provider": "google",
                "options": opts
            })
        except Exception as e:
            print(f"Supabase google_auth error: {e}")
            return None

    def sign_in_with_otp(self, email, redirect_url=None):
        """Send a one-time magic link to the user's email."""
        try:
            opts = {}
            if redirect_url:
                opts['email_redirect_to'] = redirect_url
            return self.client.auth.sign_in_with_otp({
                "email": email,
                "options": opts
            })
        except Exception as e:
            print(f"Supabase sign_in_with_otp error: {e}")
            return None

    def sign_out(self):
        try:
            return self.client.auth.sign_out()
        except Exception as e:
            print(f"Supabase sign_out error: {e}")
            return None

    def reset_password(self, email, redirect_url=None):
        try:
            opts = {}
            if redirect_url:
                opts['redirect_to'] = redirect_url
            return self.client.auth.reset_password_for_email(email, opts)
        except Exception as e:
            print(f"Supabase reset_password error: {e}")
            return None

    def get_user(self, jwt):
        try:
            return self.client.auth.get_user(jwt)
        except Exception as e:
            print(f"Supabase get_user error: {e}")
            return None

    def refresh_session(self, refresh_token):
        try:
            return self.client.auth.refresh_session(refresh_token)
        except Exception as e:
            print(f"Supabase refresh_session error: {e}")
            return None

    def exchange_code_for_session(self, code, redirect_to=None, code_verifier=None):
        """Exchange an OAuth callback code for a session."""
        try:
            print(f"Supabase: Attempting code exchange for code: {code[:5]}...")
            params = {"auth_code": code}
            if redirect_to:
                params["redirect_to"] = redirect_to
            if code_verifier:
                params["code_verifier"] = code_verifier
                print(f"Supabase: Using explicit code_verifier: {code_verifier[:5]}...")
            return self.client.auth.exchange_code_for_session(params)
        except Exception as e:
            print(f"Supabase exchange_code error: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ── Data Methods ──────────────────────────────────────────────────

    def save_blog_post(self, blog_data, user_id=None):
        try:
            post_record = {
                'user_id': user_id,
                'title': blog_data.get('title'),
                'markdown_content': blog_data.get('blog_post_markdown'),
                'html_content': blog_data.get('blog_post_html'),
                'image_header': blog_data.get('image_data'),
                'image_content': blog_data.get('image_data_2'),
                'reading_time': blog_data.get('reading_time'),
                'word_count': blog_data.get('word_count'),
                'engagement_score': blog_data.get('engagement_score'),
                'seo_score': blog_data.get('seo_score'),
                'viral_potential': blog_data.get('viral_potential'),
                'readability_score': blog_data.get('readability_score'),
                'key_quotes': json.dumps(blog_data.get('key_quotes', [])),
                'seo_recommendations': json.dumps(blog_data.get('seo_recommendations', [])),
                'created_at': datetime.utcnow().isoformat()
            }

            result = self._db_client.table('blog_posts').insert(post_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving blog post: {e}")
            return None

    def get_blog_post_by_id(self, post_id, user_id=None):
        try:
            query = self._db_client.table('blog_posts').select('*').eq('id', post_id)
            if user_id:
                query = query.eq('user_id', user_id)

            result = query.execute()
            if result.data:
                post = result.data[0]
                # Parse JSON fields safely
                for field in ('key_quotes', 'seo_recommendations'):
                    raw = post.get(field)
                    if isinstance(raw, str):
                        post[field] = json.loads(raw)
                    elif raw is None:
                        post[field] = []
                return post
            return None
        except Exception as e:
            print(f"Error retrieving blog post: {e}")
            return None

    def get_recent_posts(self, user_id=None, limit=20):
        try:
            query = self._db_client.table('blog_posts').select(
                'id, title, created_at, word_count, engagement_score, seo_score, viral_potential'
            )
            if user_id:
                query = query.eq('user_id', user_id)

            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error retrieving recent posts: {e}")
            return []

    def search_posts(self, query_str, user_id=None):
        try:
            q = self._db_client.table('blog_posts').select(
                'id, title, created_at, word_count, engagement_score'
            ).ilike('title', f'%{query_str}%')
            if user_id:
                q = q.eq('user_id', user_id)

            result = q.order('created_at', desc=True).limit(20).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error searching posts: {e}")
            return []

    def get_drafts_count(self, user_id):
        """Return the number of blog posts saved for the given user."""
        try:
            result = self._db_client.table('blog_posts').select('id', count='exact').eq('user_id', user_id).execute()
            return result.count if result.count is not None else 0
        except Exception as e:
            print(f"Error getting drafts count: {e}")
            return 0

    def delete_post(self, post_id, user_id=None):
        try:
            query = self._db_client.table('blog_posts').delete().eq('id', post_id)
            if user_id:
                query = query.eq('user_id', user_id)

            query.execute()
            return True
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False

    def get_analytics(self, user_id=None):
        try:
            query = self._db_client.table('blog_posts').select('*')
            if user_id:
                query = query.eq('user_id', user_id)

            result = query.execute()
            if not result.data:
                return {
                    'total_posts': 0,
                    'avg_engagement_score': 0,
                    'avg_seo_score': 0,
                    'avg_viral_potential': 0,
                    'total_words_written': 0,
                    'recent_posts': []
                }

            posts = result.data
            total_posts = len(posts)

            avg_engagement = sum(p.get('engagement_score', 0) for p in posts) / total_posts
            avg_seo = sum(p.get('seo_score', 0) for p in posts) / total_posts
            avg_viral = sum(p.get('viral_potential', 0) for p in posts) / total_posts
            total_words = sum(p.get('word_count', 0) for p in posts)

            return {
                'total_posts': total_posts,
                'avg_engagement_score': round(avg_engagement, 1),
                'avg_seo_score': round(avg_seo, 1),
                'avg_viral_potential': round(avg_viral, 1),
                'total_words_written': total_words,
                'recent_posts': sorted(posts, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
            }
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return None

    def update_post(self, post_id, updates, user_id=None):
        try:
            query = self._db_client.table('blog_posts').update(updates).eq('id', post_id)
            if user_id:
                query = query.eq('user_id', user_id)

            result = query.execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating post: {e}")
            return None

    def save_generation_log(self, log_data, user_id=None):
        try:
            log_record = {
                'user_id': user_id,
                'user_input': log_data.get('user_input'),
                'input_type': log_data.get('input_type'),
                'model_used': log_data.get('model'),
                'template': log_data.get('template'),
                'tone': log_data.get('tone'),
                'enhanced': log_data.get('enhanced', False),
                'success': log_data.get('success', True),
                'error_message': log_data.get('error'),
                'generation_time': log_data.get('generation_time'),
                'created_at': datetime.utcnow().isoformat()
            }

            result = self._db_client.table('generation_logs').insert(log_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving generation log: {e}")
            return None

    def get_generation_stats(self, user_id=None):
        try:
            query = self._db_client.table('generation_logs').select('*')
            if user_id:
                query = query.eq('user_id', user_id)

            result = query.execute()
            if not result.data:
                return None

            logs = result.data
            total_generations = len(logs)
            successful = sum(1 for l in logs if l.get('success', True))

            templates_used = {}
            models_used = {}
            for log in logs:
                template = log.get('template', 'default')
                templates_used[template] = templates_used.get(template, 0) + 1
                model = log.get('model_used', 'unknown')
                if model:
                    models_used[model] = models_used.get(model, 0) + 1

            top_model = max(models_used, key=models_used.get) if models_used else None

            return {
                'total_generations': total_generations,
                'successful_generations': successful,
                'failed_generations': total_generations - successful,
                'success_rate': round((successful / total_generations * 100), 1) if total_generations > 0 else 0,
                'templates_used': templates_used,
                'models_used': models_used,
                'top_model': top_model,
            }
        except Exception as e:
            print(f"Error getting generation stats: {e}")
            return None


def get_supabase_manager():
    try:
        return SupabaseManager()
    except Exception as e:
        print(f"Warning: Supabase not configured: {e}")
        return None
