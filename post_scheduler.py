import time
import threading
from datetime import datetime
from content_library import get_scheduled_posts, update_scheduled_post_status, get_post
from export_handler import export_to_medium, export_to_linkedin

class PostScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 60
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[Scheduler] Post scheduler started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[Scheduler] Post scheduler stopped")
    
    def _run(self):
        while self.running:
            try:
                self._process_scheduled_posts()
            except Exception as e:
                print(f"[Scheduler] Error processing scheduled posts: {e}")
            
            time.sleep(self.check_interval)
    
    def _process_scheduled_posts(self):
        scheduled_posts = get_scheduled_posts(status='scheduled')
        current_time = datetime.utcnow()
        
        for schedule in scheduled_posts:
            try:
                scheduled_time = datetime.fromisoformat(schedule['scheduled_time'])
                
                if current_time >= scheduled_time:
                    print(f"[Scheduler] Publishing scheduled post {schedule['post_id']}")
                    self._publish_post(schedule)
            except Exception as e:
                error_msg = f"Failed to publish: {str(e)}"
                print(f"[Scheduler] {error_msg}")
                update_scheduled_post_status(schedule['id'], 'failed', error=error_msg)
    
    def _publish_post(self, schedule):
        post = get_post(schedule['post_id'])
        if not post:
            raise Exception("Post not found")
        
        platform = schedule['publish_to']
        
        if platform == 'medium':
            result = export_to_medium(
                post['title'],
                post['markdown_content'],
                None
            )
            if result and result.get('success'):
                update_scheduled_post_status(schedule['id'], 'published')
                print(f"[Scheduler] Published to Medium: {result.get('url')}")
            else:
                raise Exception("Medium publishing failed")
        
        elif platform == 'linkedin':
            result = export_to_linkedin(
                post['title'],
                post['markdown_content'],
                None
            )
            if result and result.get('success'):
                update_scheduled_post_status(schedule['id'], 'published')
                print(f"[Scheduler] Published to LinkedIn")
            else:
                raise Exception("LinkedIn publishing failed")
        
        else:
            raise Exception(f"Unsupported platform: {platform}")

_scheduler = None

def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = PostScheduler()
    return _scheduler
