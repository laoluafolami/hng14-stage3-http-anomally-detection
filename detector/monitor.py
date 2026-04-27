import json, os, queue, threading, time
from dataclasses import dataclass, field
from typing import Optional
from config import Config
 
@dataclass
class LogEntry:
     source_ip: str
     timestamp: str
     method: str
     path: str
     status: int
     response_size: int
     raw_ts: float = field(default_factory=time.time)
 
class LogMonitor(threading.Thread):
     def __init__(self, config: Config, entry_queue: queue.Queue, stop_event: threading.Event):
         super().__init__(name='LogMonitor', daemon=True)
         self.config = config
         self.entry_queue = entry_queue
         self.stop_event = stop_event
         self.poll_interval = config.log.poll_interval_ms / 1000.0
         self.log_path = config.log.path
         self._lines_processed = 0
         self._parse_errors = 0
 
     def run(self):
         print(f'[Monitor] Watching {self.log_path}')
         while not self.stop_event.is_set():
             if os.path.exists(self.log_path): break
             print(f'[Monitor] Waiting for log file...')
             time.sleep(2)
         self._tail()
 
     def _tail(self):
         current_inode = None
         fh = None
         try:
             while not self.stop_event.is_set():
                 try:
                     stat = os.stat(self.log_path)
                     inode = stat.st_ino
                 except FileNotFoundError:
                     time.sleep(1); continue
                 if fh is None or inode != current_inode:
                     if fh: fh.close()
                     fh = open(self.log_path,  'r', encoding='utf-8', errors='replace')
                     fh.seek(0, 2)
                     current_inode = inode
                     print(f'[Monitor] Opened log file (inode={inode})')
                 while True:
                     line = fh.readline()
                     if not line: break
                     line = line.strip()
                     if not line: continue
                     entry = self._parse(line)
                     if entry:
                         self.entry_queue.put(entry)
                         self._lines_processed += 1
                 time.sleep(self.poll_interval)
         finally:
             if fh: fh.close()
 
     def _parse(self, line: str) -> Optional[LogEntry]:
         try:
             d = json.loads(line)
             raw_ip = d.get('source_ip') or d.get('remote_addr',  '0.0.0.0')
             source_ip = raw_ip.split(',')[0].strip()
             return LogEntry(
                 source_ip=source_ip, timestamp=d.get('timestamp',''),
                 method=d.get('method',''), path=d.get('path',''),
                 status=int(d.get('status', 0)),
                 response_size=int(d.get('response_size', 0)),
                 raw_ts=time.time(),
             )
         except Exception as e:
             self._parse_errors += 1
             return None
 
     @property
     def stats(self): return {'lines': self._lines_processed,  'errors': self._parse_errors}
