import math, threading, time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from config import Config
 
@dataclass
class BaselineSnapshot:
     mean: float
     stddev: float
     error_mean: float
     error_stddev: float
     sample_count: int
     last_recalc: float = field(default_factory=time.time)
     source: str =  'rolling' 
 
class BaselineEngine:
     def __init__(self, config: Config):
         self.config = config
         self._lock = threading.RLock()
         self._window_seconds = config.baseline.window_minutes * 60
         self._bucket_counts: deque = deque()
         self._error_bucket_counts: deque = deque()
         self._current_bucket = 0
         self._current_count = 0
         self._current_error_count = 0
         self._hourly_counts: Dict[int, List[float]] = defaultdict(list)
         self._hourly_error_counts: Dict[int, List[float]] = defaultdict(list)
         self._snapshot = BaselineSnapshot(
             mean=config.baseline.floor_mean,
             stddev=config.baseline.floor_stddev,
             error_mean=config.baseline.floor_mean,
             error_stddev=config.baseline.floor_stddev,
             sample_count=0)
         self._stop_event = threading.Event()
         self._thread = threading.Thread(name='BaselineEngine', target=self._loop, daemon=True)
 
     def start(self): self._thread.start(); print('[Baseline] Engine started')
     def stop(self): self._stop_event.set()
 
     def record_request(self, ts: float, is_error: bool = False):
         bucket = int(ts)
         with self._lock:
             if bucket != self._current_bucket:
                 if self._current_bucket > 0:
                     self._bucket_counts.append((self._current_bucket, self._current_count))
                     self._error_bucket_counts.append((self._current_bucket, self._current_error_count))
                     hour = self._hour_of(self._current_bucket)
                     self._hourly_counts[hour].append(self._current_count)
                     self._hourly_error_counts[hour].append(self._current_error_count)
                 self._current_bucket = bucket
                 self._current_count = 0
                 self._current_error_count = 0
             self._current_count += 1
             if is_error: self._current_error_count += 1
 
     def get_snapshot(self) -> BaselineSnapshot:
         with self._lock: return self._snapshot
 
     def _loop(self):
         interval = self.config.baseline.recalc_interval_seconds
         while not self._stop_event.is_set():
             time.sleep(interval)
             self._recalculate()
 
     def _recalculate(self):
         now = time.time()
         cutoff = now - self._window_seconds
         with self._lock:
             while self._bucket_counts and self._bucket_counts[0][0] < cutoff:
                 self._bucket_counts.popleft()
             while self._error_bucket_counts and self._error_bucket_counts[0][0] < cutoff:
                 self._error_bucket_counts.popleft()
             counts = [c for _, c in self._bucket_counts]
             error_counts = [c for _, c in self._error_bucket_counts]
             current_hour = self._hour_of(int(now))
             hourly = self._hourly_counts.get(current_hour, [])
             hourly_errors = self._hourly_error_counts.get(current_hour, [])
             source =  'rolling' 
             if len(hourly) >= self.config.baseline.min_samples:
                 counts = hourly; error_counts = hourly_errors; source =  'hourly' 
             mean, stddev = self._stats(counts)
             error_mean, error_stddev = self._stats(error_counts)
             self._snapshot = BaselineSnapshot(
                 mean=mean, stddev=stddev, error_mean=error_mean,
                 error_stddev=error_stddev, sample_count=len(counts),
                 last_recalc=now, source=source)
         print(f'[Baseline] mean={mean:.3f} stddev={stddev:.3f} samples={len(counts)} src={source}')
 
     def _stats(self, values: List[float]) -> Tuple[float, float]:
         fl_m = self.config.baseline.floor_mean
         fl_s = self.config.baseline.floor_stddev
         if not values: return fl_m, fl_s
         n = len(values)
         mean = sum(values) / n
         stddev = math.sqrt(sum((v - mean)**2 for v in values) / n)
         return max(mean, fl_m), max(stddev, fl_s)
 
     @staticmethod
     def _hour_of(ts: int) -> int:
         import datetime
         return datetime.datetime.utcfromtimestamp(ts).hour
 
     def debug_summary(self) -> dict:
         with self._lock:
             s = self._snapshot
             return {'mean': round(s.mean,4),  'stddev': round(s.stddev,4),
                      'sample_count': s.sample_count,  'source': s.source,  'last_recalc': s.last_recalc}
