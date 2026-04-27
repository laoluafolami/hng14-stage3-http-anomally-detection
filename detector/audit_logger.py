import os, threading, time
from typing import Optional
 
class AuditLogger:
     def __init__(self, audit_path: str):
         self.audit_path = audit_path
         self._lock = threading.Lock()
         os.makedirs(os.path.dirname(audit_path), exist_ok=True)
         print(f'[Audit] Writing to {audit_path}')
 
     def log_ban(self, ip, condition, rate, baseline, duration: Optional[int]):
         dur = f'{duration}s'  if duration else  'permanent' 
         self._write(f'BAN {ip} | {condition} | rate={rate:.3f} | baseline={baseline:.3f} | duration={dur}')
 
     def log_unban(self, ip, duration: Optional[int], offence_count, rate, baseline):
         dur = f'{duration}s'  if duration else  'permanent' 
         self._write(f'UNBAN {ip} | offence={offence_count} | rate={rate:.3f} | baseline={baseline:.3f} | duration={dur}')
 
     def log_baseline_recalc(self, mean, stddev, sample_count, source):
         self._write(f'BASELINE_RECALC - | source={source} | - | mean={mean:.4f},stddev={stddev:.4f},samples={sample_count} | -')
 
     def _write(self, msg):
         ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
         line = f'[{ts}] {msg}\n' 
         with self._lock:
             try:
                 with open(self.audit_path,  'a') as f: f.write(line)
                 print(f'[Audit] {line.strip()}')
             except OSError as e: print(f'[Audit] Write error: {e}')
