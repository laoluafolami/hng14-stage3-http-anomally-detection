import threading, time
from blocker import Blocker
from config import Config
from notifier import Notifier
 
class Unbanner(threading.Thread):
     def __init__(self, config: Config, blocker: Blocker, notifier: Notifier, audit, stop_event):
         super().__init__(name='Unbanner', daemon=True)
         self.config = config
         self.blocker = blocker
         self.notifier = notifier
         self.audit = audit
         self.stop_event = stop_event
 
     def run(self):
         print('[Unbanner] Started')
         while not self.stop_event.is_set():
             self._sweep()
             self.stop_event.wait(timeout=30)
 
     def _sweep(self):
         now = time.time()
         for record in self.blocker.get_active_bans():
             if record.duration_seconds is None: continue
             if now - record.banned_at >= record.duration_seconds:
                 self._release(record, now)
 
     def _release(self, record, now):
         old = self.blocker.unban(record.ip)
         if not old: return
         next_i = old.offence_count
         backoff = self.config.unban.backoff_seconds
         next_info =  'permanent'  if next_i >= len(backoff) else f'{backoff[next_i]}s' 
         dur_str = self._human(old.duration_seconds)
         print(f'[Unbanner] Released {record.ip} after {dur_str}')
         self.notifier.send_unban(ip=record.ip, ban_duration=dur_str,
                                  offence_count=old.offence_count, next_info=next_info, timestamp=now)
         self.audit.log_unban(ip=record.ip, duration=old.duration_seconds,
                              offence_count=old.offence_count, rate=old.rate, baseline=old.baseline_mean)
 
     @staticmethod
     def _human(s): return f'{s//3600}h'  if s>=3600 else f'{s//60}m'  if s>=60 else f'{s}s' 
import threading, time
from blocker import Blocker
from config import Config
from notifier import Notifier
 
class Unbanner(threading.Thread):
     def __init__(self, config: Config, blocker: Blocker, notifier: Notifier, audit, stop_event):
         super().__init__(name='Unbanner', daemon=True)
         self.config = config
         self.blocker = blocker
         self.notifier = notifier
         self.audit = audit
         self.stop_event = stop_event
 
     def run(self):
         print('[Unbanner] Started')
         while not self.stop_event.is_set():
             self._sweep()
             self.stop_event.wait(timeout=30)
 
     def _sweep(self):
         now = time.time()
         for record in self.blocker.get_active_bans():
             if record.duration_seconds is None: continue
             if now - record.banned_at >= record.duration_seconds:
                 self._release(record, now)
 
     def _release(self, record, now):
         old = self.blocker.unban(record.ip)
         if not old: return
         next_i = old.offence_count
         backoff = self.config.unban.backoff_seconds
         next_info =  'permanent'  if next_i >= len(backoff) else f'{backoff[next_i]}s' 
         dur_str = self._human(old.duration_seconds)
         print(f'[Unbanner] Released {record.ip} after {dur_str}')
         self.notifier.send_unban(ip=record.ip, ban_duration=dur_str,
                                  offence_count=old.offence_count, next_info=next_info, timestamp=now)
         self.audit.log_unban(ip=record.ip, duration=old.duration_seconds,
                              offence_count=old.offence_count, rate=old.rate, baseline=old.baseline_mean)
 
     @staticmethod
     def _human(s): return f'{s//3600}h'  if s>=3600 else f'{s//60}m'  if s>=60 else f'{s}s' 
