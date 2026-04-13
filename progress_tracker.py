import json
import time
from collections import defaultdict
from threading import Lock
from tenant_context import current_tenant_id, normalize_tenant_id

class ProgressTracker:
    def __init__(self):
        self.progress_data = defaultdict(dict)
        self.lock = Lock()
    
    def _key(self, job_id: str, tenant_id=None):
        tenant_id = normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'
        return f'{tenant_id}:{job_id}'

    def update_progress(self, job_id: str, stage: str, progress: int, message: str = "", tenant_id=None):
        with self.lock:
            self.progress_data[self._key(job_id, tenant_id)] = {
                'stage': stage,
                'progress': progress,
                'message': message,
                'timestamp': time.time(),
                'tenant_id': normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'
            }
    
    def get_progress(self, job_id: str, tenant_id=None):
        with self.lock:
            return self.progress_data.get(self._key(job_id, tenant_id))
    
    def remove_progress(self, job_id: str, tenant_id=None):
        with self.lock:
            key = self._key(job_id, tenant_id)
            if key in self.progress_data:
                del self.progress_data[key]
    
    def cleanup_old_progress(self, max_age_seconds: int = 3600):
        current_time = time.time()
        with self.lock:
            jobs_to_remove = []
            for job_id, data in self.progress_data.items():
                if current_time - data['timestamp'] > max_age_seconds:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.progress_data[job_id]

_progress_tracker = None

def get_progress_tracker():
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
