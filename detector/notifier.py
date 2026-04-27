import json, threading, time
from typing import Optional
import requests
from config import Config
 
class Notifier:
     def __init__(self, config: Config):
         self.config = config
         self.webhook_url = config.slack.webhook_url
         self.enabled = config.slack.enabled
         self.timeout = config.slack.timeout_seconds
 
     def send_ban(self, ip, condition, rate, baseline_mean, baseline_stddev, z_score, ban_duration, timestamp):
         dur = ban_duration or  'PERMANENT' 
         blocks = [
             {'type':'header','text':{'type':'plain_text','text':'🚨 IP BANNED — Anomaly Detected'}},
             {'type':'section','fields':[
                 {'type':'mrkdwn','text':f'*IP:*\n`{ip}`'},
                 {'type':'mrkdwn','text':f'*Duration:*\n{dur}'},
                 {'type':'mrkdwn','text':f'*Rate:*\n{rate:.2f} req/s'},
                 {'type':'mrkdwn','text':f'*Baseline:*\n{baseline_mean:.2f} req/s'},
                 {'type':'mrkdwn','text':f'*StdDev:*\n{baseline_stddev:.2f}'},
                 {'type':'mrkdwn','text':f'*Z-Score:*\n{z_score:.2f}'},
             ]},
             {'type':'section','text':{'type':'mrkdwn','text':f'*Condition:* {condition}'}},
             {'type':'context','elements':[{'type':'mrkdwn','text':f'Detected at {self._ts(timestamp)}'}]},
         ]
         self._dispatch({'blocks':blocks,'text':f'IP {ip} banned ({condition})'})
 
     def send_unban(self, ip, ban_duration, offence_count, next_info, timestamp):
         blocks = [
             {'type':'header','text':{'type':'plain_text','text':'✅ IP UNBANNED — Ban Expired'}},
             {'type':'section','fields':[
                 {'type':'mrkdwn','text':f'*IP:*\n`{ip}`'},
                 {'type':'mrkdwn','text':f'*Served:*\n{ban_duration}'},
                 {'type':'mrkdwn','text':f'*Offences:*\n{offence_count}'},
                 {'type':'mrkdwn','text':f'*Next:*\n{next_info}'},
             ]},
             {'type':'context','elements':[{'type':'mrkdwn','text':f'Released at {self._ts(timestamp)}'}]},
         ]
         self._dispatch({'blocks':blocks,'text':f'{ip} unbanned after {ban_duration}'})
 
     def send_global_alert(self, rate, baseline_mean, baseline_stddev, z_score, condition, timestamp):
         blocks = [
             {'type':'header','text':{'type':'plain_text','text':'🌐 GLOBAL TRAFFIC SPIKE'}},
             {'type':'section','fields':[
                 {'type':'mrkdwn','text':f'*Global Rate:*\n{rate:.2f} req/s'},
                 {'type':'mrkdwn','text':f'*Baseline:*\n{baseline_mean:.2f} req/s'},
                 {'type':'mrkdwn','text':f'*StdDev:*\n{baseline_stddev:.2f}'},
                 {'type':'mrkdwn','text':f'*Z-Score:*\n{z_score:.2f}'},
             ]},
             {'type':'section','text':{'type':'mrkdwn','text':f'*Condition:* {condition}\n_No single IP exceeded threshold. Monitoring all sources._'}},
             {'type':'context','elements':[{'type':'mrkdwn','text':f'Detected at {self._ts(timestamp)}'}]},
         ]
         self._dispatch({'blocks':blocks,'text':f'Global spike: {rate:.2f} req/s'})
 
     def _dispatch(self, payload):
         if not self.enabled:
             print(f'[Notifier] Slack disabled: {payload.get("text","")}')
             return
         threading.Thread(target=self._send, args=(payload,), daemon=True).start()
 
     def _send(self, payload):
         try:
             r = requests.post(self.webhook_url, data=json.dumps(payload),
                               headers={'Content-Type':'application/json'}, timeout=self.timeout)
             print(f'[Notifier] Slack {r.status_code}: {payload.get("text","")[:60]}')
         except Exception as e: print(f'[Notifier] Slack error: {e}')
 
     @staticmethod
     def _ts(ts): import datetime; return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
