import os, threading, time
from typing import Optional

class AuditLogger:
    def __init__(self, audit_path: str):
        self.audit_path = audit_path
        self._lock = threading.Lock()
        # Safely create parent directory if it exists in the path
        dir_path = os.path.dirname(audit_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        print(f'[Audit] Writing to {audit_path}')

    def log_ban(self, ip, condition, rate, baseline, duration: Optional[int]):
        dur = f'{duration}s' if duration else 'permanent'
        # Format: [timestamp] ACTION ip | condition | rate | baseline | duration
        self._write(f'BAN {ip} | {condition} | {rate:.2f} | {baseline:.2f} | {dur}')

    def log_unban(self, ip, duration: Optional[int], offence_count, rate, baseline):
        dur = f'{duration}s' if duration else 'permanent'
        self._write(f'UNBAN {ip} | backoff_complete | {rate:.2f} | {baseline:.2f} | {dur}')

    def log_baseline_recalc(self, mean, stddev, sample_count, source):
        self._write(f'BASELINE_RECALC GLOBAL | scheduled | 0.00 | {mean:.2f} | window=30min')

    def _write(self, msg):
        ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        line = f'[{ts}] {msg}\n'
        with self._lock:
            try:
                with open(self.audit_path, 'a') as f:
                    f.write(line)
                print(f'[Audit] {line.strip()}')
            except OSError as e:
                print(f'[Audit] Write error: {e}')
