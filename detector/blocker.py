import subprocess, threading, time
from dataclasses import dataclass
from typing import Dict, List, Optional
from config import Config
 
@dataclass
class BanRecord:
     ip: str
     banned_at: float
     duration_seconds: Optional[int]
     offence_count: int
     condition: str
     rate: float
     baseline_mean: float
 
class Blocker:
     def __init__(self, config: Config):
         self.config = config
         self._lock = threading.Lock()
         self._bans: Dict[str, BanRecord] = {}
         self._offence_counts: Dict[str, int] = {}
 
     def ban(self, ip, condition, rate, baseline_mean) -> BanRecord:
         with self._lock:
             offences = self._offence_counts.get(ip, 0)
             self._offence_counts[ip] = offences + 1
             backoff = self.config.unban.backoff_seconds
             duration = None if offences >= len(backoff) else backoff[offences]
             record = BanRecord(ip=ip, banned_at=time.time(), duration_seconds=duration,
                                offence_count=offences+1, condition=condition,
                                rate=rate, baseline_mean=baseline_mean)
             self._bans[ip] = record
         self._ipt_add(ip)
         print(f'[Blocker] BANNED {ip} dur={duration}s offence={offences+1}')
         return record
 
     def unban(self, ip) -> Optional[BanRecord]:
         with self._lock: record = self._bans.pop(ip, None)
         if record: self._ipt_del(ip); print(f'[Blocker] UNBANNED {ip}')
         return record
 
     def is_banned(self, ip): return ip in self._bans
     def get_active_bans(self) -> List[BanRecord]:
         with self._lock: return list(self._bans.values())
 
     def _ipt_add(self, ip):
         try:
             subprocess.run(['iptables','-I','INPUT','-s',ip,'-j','DROP'],
                            check=True, capture_output=True, timeout=5)
             print(f'[Blocker] iptables DROP {ip} added')
         except Exception as e: print(f'[Blocker] iptables add error: {e}')
 
     def _ipt_del(self, ip):
         try:
             subprocess.run(['iptables','-D','INPUT','-s',ip,'-j','DROP'],
                            check=True, capture_output=True, timeout=5)
         except Exception as e: print(f'[Blocker] iptables del note: {e}')
