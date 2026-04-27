from dataclasses import dataclass
from typing import List
import yaml
 
@dataclass
class LogConfig:
     path: str
     audit_path: str
     poll_interval_ms: int
 
@dataclass
class WindowConfig:
     per_ip_seconds: int
     global_seconds: int
 
@dataclass
class BaselineConfig:
     window_minutes: int
     recalc_interval_seconds: int
     min_samples: int
     floor_mean: float
     floor_stddev: float
     hourly_slots: int
 
@dataclass
class DetectionConfig:
     z_score_threshold: float
     rate_multiplier: float
     error_rate_multiplier: float
     tightened_z_score: float
 
@dataclass
class UnbanConfig:
     backoff_seconds: List[int]
     permanent_after: int
 
@dataclass
class SlackConfig:
     webhook_url: str
     enabled: bool
     timeout_seconds: int
 
@dataclass
class DashboardConfig:
     host: str
     port: int
     refresh_interval_seconds: int
     top_ips_count: int
 
@dataclass
class Config:
     log: LogConfig
     window: WindowConfig
     baseline: BaselineConfig
     detection: DetectionConfig
     unban: UnbanConfig
     slack: SlackConfig
     dashboard: DashboardConfig
 
     @classmethod
     def load(cls, path='config.yaml') ->  'Config':
         with open(path) as f:
             raw = yaml.safe_load(f)
         return cls(
             log=LogConfig(**raw['log']),
             window=WindowConfig(**raw['window']),
             baseline=BaselineConfig(**raw['baseline']),
             detection=DetectionConfig(**raw['detection']),
             unban=UnbanConfig(**raw['unban']),
             slack=SlackConfig(**raw['slack']),
             dashboard=DashboardConfig(**raw['dashboard']),
         )
