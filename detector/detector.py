import queue, threading, time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from baseline import BaselineEngine, BaselineSnapshot
from config import Config
from monitor import LogEntry
 
@dataclass
class AnomalyEvent:
     kind: str
     ip: Optional[str]
     current_rate: float
     baseline_mean: float
     baseline_stddev: float
     z_score: float
     condition: str
     timestamp: float = field(default_factory=time.time)
 
class SlidingWindow:
     def __init__(self, window_seconds: int):
         self.window_seconds = window_seconds
         self._deque: deque = deque()
         self._error_deque: deque = deque()
         self._lock = threading.Lock()
 
     def record(self, ts: float, is_error: bool = False):
         with self._lock:
             self._deque.append(ts)
             if is_error: self._error_deque.append(ts)
 
     def rate(self, now: Optional[float] = None) -> float:
         now = now or time.time()
         cutoff = now - self.window_seconds
         with self._lock:
             while self._deque and self._deque[0] < cutoff: self._deque.popleft()
             return len(self._deque) / self.window_seconds
 
     def error_rate(self, now: Optional[float] = None) -> float:
         now = now or time.time()
         cutoff = now - self.window_seconds
         with self._lock:
             while self._error_deque and self._error_deque[0] < cutoff: self._error_deque.popleft()
             return len(self._error_deque) / self.window_seconds
 
class AnomalyDetector(threading.Thread):
     def __init__(self, config, baseline, entry_queue, anomaly_queue, stop_event):
         super().__init__(name='AnomalyDetector', daemon=True)
         self.config = config
         self.baseline = baseline
         self.entry_queue = entry_queue
         self.anomaly_queue = anomaly_queue
         self.stop_event = stop_event
         self._ip_windows: Dict[str, SlidingWindow] = defaultdict(
             lambda: SlidingWindow(config.window.per_ip_seconds))
         self._global_window = SlidingWindow(config.window.global_seconds)
         self._flagged_ips: Dict[str, float] = {}
         self._global_flagged_at: Optional[float] = None
         self.ip_request_counts: Dict[str, int] = defaultdict(int)
         self._lock = threading.Lock()
 
     def run(self):
         print('[Detector] Running')
         while not self.stop_event.is_set():
             try:
                 entry: LogEntry = self.entry_queue.get(timeout=1.0)
                 self._process(entry)
             except queue.Empty: continue
 
     def _process(self, entry: LogEntry):
         now = entry.raw_ts
         ip = entry.source_ip
         is_error = entry.status >= 400
         self.baseline.record_request(now, is_error)
         self._ip_windows[ip].record(now, is_error)
         self._global_window.record(now, is_error)
         with self._lock: self.ip_request_counts[ip] += 1
         snap = self.baseline.get_snapshot()
         self._check_ip(ip, self._ip_windows[ip].rate(now), self._ip_windows[ip].error_rate(now), snap, now)
         self._check_global(self._global_window.rate(now), snap, now)
 
     def _check_ip(self, ip, rate, error_rate, snap, now):
         z_thresh = self.config.detection.z_score_threshold
         error_surge = error_rate > self.config.detection.error_rate_multiplier * snap.error_mean
         if error_surge: z_thresh = self.config.detection.tightened_z_score
         z, cond = self._evaluate(rate, snap.mean, snap.stddev, z_thresh)
         if cond is None: return
         if now - self._flagged_ips.get(ip, 0) < self.config.window.per_ip_seconds: return
         self._flagged_ips[ip] = now
         if error_surge: cond +=  ' [error-surge]' 
         self.anomaly_queue.put(AnomalyEvent('per_ip', ip, rate, snap.mean, snap.stddev, z, cond))
         print(f'[Detector] PER-IP ip={ip} rate={rate:.2f} mean={snap.mean:.2f} z={z:.2f}')
 
     def _check_global(self, rate, snap, now):
         z, cond = self._evaluate(rate, snap.mean, snap.stddev, self.config.detection.z_score_threshold)
         if cond is None: return
         if self._global_flagged_at and now - self._global_flagged_at < self.config.window.global_seconds: return
         self._global_flagged_at = now
         self.anomaly_queue.put(AnomalyEvent('global', None, rate, snap.mean, snap.stddev, z, cond))
         print(f'[Detector] GLOBAL rate={rate:.2f} mean={snap.mean:.2f} z={z:.2f}')
 
     def _evaluate(self, rate, mean, stddev, z_thresh) -> Tuple[float, Optional[str]]:
         z = (rate - mean) / stddev
         if z > z_thresh: return z, f'z_score={z:.2f} > threshold={z_thresh:.2f}' 
         if mean > 0 and rate > self.config.detection.rate_multiplier * mean:
             return z, f'rate={rate:.2f} > {self.config.detection.rate_multiplier}x mean={mean:.2f}' 
         return z, None
 
     def get_top_ips(self, n=10):
         with self._lock:
             return sorted(self.ip_request_counts.items(), key=lambda x: x[1], reverse=True)[:n]
 
     def get_global_rate(self): return self._global_window.rate()
