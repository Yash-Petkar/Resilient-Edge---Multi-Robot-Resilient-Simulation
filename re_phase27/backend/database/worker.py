"""Non-blocking SQLite persistence worker for simulation writes."""
from __future__ import annotations
import logging, queue, threading, time
logger=logging.getLogger('resilientedge.persistence.worker')
class PersistenceWorker:
    def __init__(self,persistence):
        self.persistence=persistence; self.q=queue.Queue(maxsize=5000); self._stop=threading.Event(); self.thread=threading.Thread(target=self._run,daemon=True,name='resilientedge-persistence'); self.thread.start()
    def submit(self,method,*args,**kwargs):
        try:self.q.put_nowait((method,args,kwargs))
        except queue.Full: logger.warning('Persistence queue full; dropping non-critical write: %s',method)
    def _run(self):
        while not self._stop.is_set():
            try: method,args,kwargs=self.q.get(timeout=.5)
            except queue.Empty: continue
            delay=.25
            for attempt in range(4):
                try:
                    getattr(self.persistence,method)(*args,**kwargs); break
                except Exception as exc:
                    if attempt==3: logger.error('Persistence failed for %s after retries: %s',method,exc)
                    else: time.sleep(delay); delay=min(delay*2,2)
            self.q.task_done()
    def stop(self): self._stop.set(); self.thread.join(timeout=2)
