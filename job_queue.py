import os
import json
import time
import uuid
from datetime import datetime
from threading import Thread, Lock
from queue import Queue, Empty
from typing import Optional, Dict, Callable, Any
from tenant_context import current_tenant_id, normalize_tenant_id

class JobQueue:
    def __init__(self):
        self.queue = Queue()
        self.jobs = {}
        self.lock = Lock()
        self.workers = []
        self.running = True
        self.num_workers = int(os.environ.get('JOB_WORKERS', '2'))
        
        self._start_workers()
        print(f"[JobQueue] Started with {self.num_workers} workers")
    
    def _start_workers(self):
        for i in range(self.num_workers):
            worker = Thread(target=self._worker, args=(i,), daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker(self, worker_id: int):
        print(f"[JobQueue] Worker {worker_id} started")
        while self.running:
            try:
                job_id = self.queue.get(timeout=1)
                if job_id is None:
                    continue
                
                with self.lock:
                    if job_id not in self.jobs:
                        continue
                    job = self.jobs[job_id]
                
                if job['status'] == 'pending':
                    self._execute_job(job_id, job, worker_id)
                
                self.queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"[JobQueue] Worker {worker_id} error: {e}")
    
    def _execute_job(self, job_id: str, job: dict, worker_id: int):
        try:
            with self.lock:
                job['status'] = 'processing'
                job['started_at'] = datetime.utcnow().isoformat()
                job['worker_id'] = worker_id
            
            print(f"[JobQueue] Worker {worker_id} processing job {job_id}")
            
            func = job['function']
            args = job.get('args', [])
            kwargs = job.get('kwargs', {})
            callback = job.get('callback')
            progress_callback = job.get('progress_callback')
            
            if progress_callback:
                kwargs['progress_callback'] = lambda p: self.update_progress(job_id, p, tenant_id=job.get('tenant_id'))
            
            result = func(*args, **kwargs)
            
            with self.lock:
                job['status'] = 'completed'
                job['completed_at'] = datetime.utcnow().isoformat()
                job['result'] = result
                job['progress'] = 100
            
            if callback:
                try:
                    callback(result)
                except Exception as cb_error:
                    print(f"[JobQueue] Callback error: {cb_error}")
            
            print(f"[JobQueue] Job {job_id} completed")
            
        except Exception as e:
            error_msg = str(e)
            print(f"[JobQueue] Job {job_id} failed: {error_msg}")
            
            with self.lock:
                job['status'] = 'failed'
                job['completed_at'] = datetime.utcnow().isoformat()
                job['error'] = error_msg
    
    def enqueue(self, func: Callable, args: tuple = (), kwargs: dict = None, 
                callback: Callable = None, priority: int = 0, 
                job_type: str = 'default', tenant_id: str = None) -> str:
        job_id = str(uuid.uuid4())
        tenant_id = normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'
        
        job = {
            'id': job_id,
            'function': func,
            'args': args,
            'kwargs': kwargs or {},
            'callback': callback,
            'priority': priority,
            'job_type': job_type,
            'status': 'pending',
            'progress': 0,
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'worker_id': None,
            'tenant_id': tenant_id
        }
        
        with self.lock:
            self.jobs[job_id] = job
        
        self.queue.put(job_id)
        print(f"[JobQueue] Job {job_id} enqueued (type: {job_type})")
        
        return job_id
    
    def get_job_status(self, job_id: str, tenant_id: str = None) -> Optional[dict]:
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id].copy()
            if tenant_id and normalize_tenant_id(job.get('tenant_id')) != normalize_tenant_id(tenant_id):
                return None
            job.pop('function', None)
            job.pop('callback', None)
            job.pop('args', None)
            job.pop('kwargs', None)
            
            return job
    
    def update_progress(self, job_id: str, progress: int, tenant_id: str = None):
        with self.lock:
            if job_id in self.jobs and (not tenant_id or normalize_tenant_id(self.jobs[job_id].get('tenant_id')) == normalize_tenant_id(tenant_id)):
                self.jobs[job_id]['progress'] = min(max(progress, 0), 100)
    
    def cancel_job(self, job_id: str, tenant_id: str = None) -> bool:
        with self.lock:
            if job_id in self.jobs and (not tenant_id or normalize_tenant_id(self.jobs[job_id].get('tenant_id')) == normalize_tenant_id(tenant_id)):
                job = self.jobs[job_id]
                if job['status'] == 'pending':
                    job['status'] = 'cancelled'
                    job['completed_at'] = datetime.utcnow().isoformat()
                    return True
        return False
    
    def get_queue_stats(self, tenant_id: str = None) -> dict:
        with self.lock:
            jobs = [j for j in self.jobs.values() if not tenant_id or normalize_tenant_id(j.get('tenant_id')) == normalize_tenant_id(tenant_id)]
            pending = sum(1 for j in jobs if j['status'] == 'pending')
            processing = sum(1 for j in jobs if j['status'] == 'processing')
            completed = sum(1 for j in jobs if j['status'] == 'completed')
            failed = sum(1 for j in jobs if j['status'] == 'failed')
            
            return {
                'total_jobs': len(jobs),
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'failed': failed,
                'workers': self.num_workers,
                'queue_size': self.queue.qsize()
            }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        current_time = datetime.utcnow()
        with self.lock:
            jobs_to_remove = []
            for job_id, job in self.jobs.items():
                if job['status'] in ['completed', 'failed', 'cancelled']:
                    if job.get('completed_at'):
                        completed_time = datetime.fromisoformat(job['completed_at'])
                        age_hours = (current_time - completed_time).total_seconds() / 3600
                        if age_hours > max_age_hours:
                            jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
            
            if jobs_to_remove:
                print(f"[JobQueue] Cleaned up {len(jobs_to_remove)} old jobs")
    
    def shutdown(self):
        print("[JobQueue] Shutting down...")
        self.running = False
        for _ in range(self.num_workers):
            self.queue.put(None)
        for worker in self.workers:
            worker.join(timeout=5)

_job_queue = None

def get_job_queue() -> JobQueue:
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue()
    return _job_queue
