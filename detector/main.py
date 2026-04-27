import queue, signal, sys, threading, time
from audit_logger import AuditLogger
from baseline import BaselineEngine
from blocker import Blocker
from config import Config
from dashboard import Dashboard
from detector import AnomalyDetector, AnomalyEvent
from monitor import LogMonitor
from notifier import Notifier
from unbanner import Unbanner
 
def main():
     print('='*50)
     print(' HNG Stage 4 — Anomaly Detector Starting')
     print('='*50)
     config = Config.load('/app/config.yaml')
     entry_queue = queue.Queue(maxsize=50_000)
     anomaly_queue = queue.Queue(maxsize=1_000)
     stop_event = threading.Event()
     audit = AuditLogger(config.log.audit_path)
     baseline = BaselineEngine(config)
     blocker = Blocker(config)
     notifier = Notifier(config)
     monitor = LogMonitor(config, entry_queue, stop_event)
     detector = AnomalyDetector(config, baseline, entry_queue, anomaly_queue, stop_event)
     unbanner = Unbanner(config, blocker, notifier, audit, stop_event)
     dashboard = Dashboard(config, baseline, blocker, detector)
     _patch_audit(baseline, audit)
     def _shutdown(sig, frame):
         print('\n[Main] Shutting down...')
         stop_event.set()
     signal.signal(signal.SIGINT, _shutdown)
     signal.signal(signal.SIGTERM, _shutdown)
     baseline.start(); monitor.start(); detector.start()
     unbanner.start(); dashboard.start()
     print('[Main] All threads started. Entering response loop.')
     while not stop_event.is_set():
         try:
             event: AnomalyEvent = anomaly_queue.get(timeout=1.0)
             _handle(event, config, blocker, notifier, audit)
         except queue.Empty: continue
     print('[Main] Stopped.')
     sys.exit(0)
 
def _handle(event, config, blocker, notifier, audit):
     if event.kind ==  'per_ip':
         ip = event.ip
         if blocker.is_banned(ip): return
         record = blocker.ban(ip=ip, condition=event.condition,
                              rate=event.current_rate, baseline_mean=event.baseline_mean)
         dur = f'{record.duration_seconds}s'  if record.duration_seconds else  'permanent' 
         notifier.send_ban(ip=ip, condition=event.condition, rate=event.current_rate,
                           baseline_mean=event.baseline_mean, baseline_stddev=event.baseline_stddev,
                           z_score=event.z_score, ban_duration=dur, timestamp=event.timestamp)
         audit.log_ban(ip=ip, condition=event.condition, rate=event.current_rate,
                       baseline=event.baseline_mean, duration=record.duration_seconds)
     elif event.kind ==  'global':
         notifier.send_global_alert(rate=event.current_rate, baseline_mean=event.baseline_mean,
                                    baseline_stddev=event.baseline_stddev, z_score=event.z_score,
                                    condition=event.condition, timestamp=event.timestamp)
         audit.log_ban(ip='GLOBAL', condition=event.condition, rate=event.current_rate,
                       baseline=event.baseline_mean, duration=None)
 
def _patch_audit(baseline, audit):
     orig = baseline._recalculate
     def patched():
         orig()
         s = baseline.get_snapshot()
         audit.log_baseline_recalc(mean=s.mean, stddev=s.stddev,
                                    sample_count=s.sample_count, source=s.source)
     baseline._recalculate = patched
 
if __name__ ==  '__main__': main()
