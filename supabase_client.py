import os
from supabase import create_client, Client
from datetime import datetime
import json

class SupabaseManager:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        self.client: Client = create_client(url, key)
    
    def save_blog_post(self, blog_data):
        try:
            post_record = {
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
            
            result = self.client.table('blog_posts').insert(post_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving blog post: {e}")
            return None
    
    def get_blog_post_by_id(self, post_id):
        try:
            result = self.client.table('blog_posts').select('*').eq('id', post_id).execute()
            if result.data:
                post = result.data[0]
                post['key_quotes'] = json.loads(post.get('key_quotes', '[]'))
                post['seo_recommendations'] = json.loads(post.get('seo_recommendations', '[]'))
                return post
            return None
        except Exception as e:
            print(f"Error retrieving blog post: {e}")
            return None
    
    def get_recent_posts(self, limit=20):
        try:
            result = self.client.table('blog_posts').select('id, title, created_at, word_count, engagement_score, seo_score, viral_potential').order('created_at', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error retrieving recent posts: {e}")
            return []
    
    def search_posts(self, query):
        try:
            result = self.client.table('blog_posts').select('id, title, created_at, word_count, engagement_score').ilike('title', f'%{query}%').order('created_at', desc=True).limit(20).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error searching posts: {e}")
            return []
    
    def delete_post(self, post_id):
        try:
            result = self.client.table('blog_posts').delete().eq('id', post_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False
    
    def get_analytics(self):
        try:
            result = self.client.table('blog_posts').select('*').execute()
            if not result.data:
                return None
            
            posts = result.data
            total_posts = len(posts)
            
            avg_engagement = sum(p.get('engagement_score', 0) for p in posts) / total_posts if total_posts > 0 else 0
            avg_seo = sum(p.get('seo_score', 0) for p in posts) / total_posts if total_posts > 0 else 0
            avg_viral = sum(p.get('viral_potential', 0) for p in posts) / total_posts if total_posts > 0 else 0
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
    
    def update_post(self, post_id, updates):
        try:
            result = self.client.table('blog_posts').update(updates).eq('id', post_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating post: {e}")
            return None
    
    def save_generation_log(self, log_data):
        try:
            log_record = {
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
            
            result = self.client.table('generation_logs').insert(log_record).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving generation log: {e}")
            return None
    
    def get_generation_stats(self):
        try:
            result = self.client.table('generation_logs').select('*').execute()
            if not result.data:
                return None
            
            logs = result.data
            total_generations = len(logs)
            successful = sum(1 for l in logs if l.get('success', True))
            
            templates_used = {}
            for log in logs:
                template = log.get('template', 'default')
                templates_used[template] = templates_used.get(template, 0) + 1
            
            return {
                'total_generations': total_generations,
                'successful_generations': successful,
                'failed_generations': total_generations - successful,
                'success_rate': round((successful / total_generations * 100), 1) if total_generations > 0 else 0,
                'templates_used': templates_used
            }
        except Exception as e:
            print(f"Error getting generation stats: {e}")
            return None

_supabase_manager = None

def get_supabase_manager():
    global _supabase_manager
    if _supabase_manager is None:
        try:
            _supabase_manager = SupabaseManager()
        except Exception as e:
            print(f"Warning: Supabase not configured: {e}")
            _supabase_manager = None
    return _supabase_manager
