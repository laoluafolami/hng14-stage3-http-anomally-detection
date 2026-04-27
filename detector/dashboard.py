import os, threading, time
import psutil
from flask import Flask, jsonify, render_template_string
from config import Config
 
# ── Full HTML dashboard ──────────────────────────────────────────────────
DASHBOARD_HTML =  '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"  content="width=device-width, initial-scale=1.0">
<title>HNG Anomaly Detector</title>
<style>
   @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
   :root {
     --bg: #0a0e1a; --surface: #111827; --surface2: #1f2937;
     --border: #374151; --text: #f9fafb; --muted: #9ca3af;
     --blue: #3b82f6; --teal: #14b8a6; --green: #22c55e;
     --red: #ef4444; --amber: #f59e0b; --purple: #a855f7;
     --glow-blue: 0 0 20px rgba(59,130,246,0.3);
     --glow-red:  0 0 20px rgba(239,68,68,0.3);
   }
   * { box-sizing:border-box; margin:0; padding:0; }
   body { background:var(--bg); color:var(--text); font-family:'Inter',sans-serif;
          min-height:100vh; }
   /* Top bar */
   .topbar { background:linear-gradient(135deg,#0f172a,#1e293b);
     border-bottom:1px solid var(--border); padding:16px 24px;
     display:flex; justify-content:space-between; align-items:center;
     position:sticky; top:0; z-index:100; backdrop-filter:blur(10px); }
   .logo { display:flex; align-items:center; gap:12px; }
   .logo-icon { width:36px; height:36px; background:linear-gradient(135deg,var(--blue),var(--teal));
     border-radius:8px; display:flex; align-items:center; justify-content:center;
     font-size:18px; box-shadow:var(--glow-blue); }
   .logo-text { font-size:1.1rem; font-weight:700; color:var(--text); }
   .logo-sub  { font-size:0.72rem; color:var(--muted); font-weight:400; }
   .topbar-right { display:flex; align-items:center; gap:20px; }
   .live-badge { display:flex; align-items:center; gap:6px; background:rgba(34,197,94,0.1);
     border:1px solid rgba(34,197,94,0.3); border-radius:20px; padding:4px 12px; font-size:0.75rem; color:var(--green); }
   .pulse { width:8px; height:8px; background:var(--green); border-radius:50%;
     animation:pulse 1.5s infinite; }
   @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.3)} }
   .uptime-text { font-size:0.8rem; color:var(--muted); font-family:'JetBrains Mono',monospace; }
   /* Stat cards */
   .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; padding:24px; }
   .card { background:var(--surface); border:1px solid var(--border); border-radius:12px;
     padding:20px; position:relative; overflow:hidden; transition:transform 0.2s,box-shadow 0.2s; }
   .card:hover { transform:translateY(-2px); box-shadow:0 8px 25px rgba(0,0,0,0.4); }
   .card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px;
     background:linear-gradient(90deg,var(--blue),var(--teal)); }
   .card.danger::before { background:linear-gradient(90deg,var(--red),var(--amber)); }
   .card.success::before { background:linear-gradient(90deg,var(--green),var(--teal)); }
   .card.warn::before { background:linear-gradient(90deg,var(--amber),var(--red)); }
   .card-label { font-size:0.72rem; color:var(--muted); text-transform:uppercase;
     letter-spacing:0.08em; font-weight:500; }
   .card-value { font-size:2.4rem; font-weight:700; margin:8px 0 4px;
     font-family:'JetBrains Mono',monospace; line-height:1; }
   .card-value.good  { color:var(--green); }
   .card-value.bad   { color:var(--red); text-shadow:var(--glow-red); }
   .card-value.warn  { color:var(--amber); }
   .card-value.info  { color:var(--blue); }
   .card-sub { font-size:0.75rem; color:var(--muted); }
   .card-icon { position:absolute; top:16px; right:16px; font-size:1.8rem; opacity:0.15; }
   /* Progress bar */
   .progress-bar { height:6px; background:var(--border); border-radius:3px; margin-top:8px; }
   .progress-fill { height:100%; border-radius:3px; transition:width 0.5s ease; }
   .fill-green { background:linear-gradient(90deg,var(--green),var(--teal)); }
   .fill-amber { background:linear-gradient(90deg,var(--amber),var(--red)); }
   .fill-red   { background:linear-gradient(90deg,var(--red),#c026d3); }
   /* Sections */
   .section { padding:0 24px 24px; }
   .section-header { display:flex; justify-content:space-between; align-items:center;
     padding:12px 0; border-bottom:1px solid var(--border); margin-bottom:16px; }
   .section-title { font-size:0.9rem; font-weight:600; color:var(--text); }
   .section-badge { background:var(--surface2); border:1px solid var(--border);
     border-radius:20px; padding:3px 10px; font-size:0.75rem; color:var(--muted); }
   /* Tables */
   .data-table { width:100%; border-collapse:collapse; font-size:0.82rem; }
   .data-table th { text-align:left; padding:10px 14px; color:var(--muted);
     font-weight:500; border-bottom:1px solid var(--border); font-size:0.75rem;
     text-transform:uppercase; letter-spacing:0.05em; }
   .data-table td { padding:12px 14px; border-bottom:1px solid rgba(55,65,81,0.4); }
   .data-table tr:hover td { background:rgba(255,255,255,0.02); }
   .data-table tr:last-child td { border-bottom:none; }
   code { font-family:'JetBrains Mono',monospace; font-size:0.82em;
     background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.2);
     border-radius:4px; padding:2px 7px; color:var(--blue); }
   /* Badges */
   .badge { display:inline-flex; align-items:center; gap:5px; padding:3px 10px;
     border-radius:20px; font-size:0.72rem; font-weight:600; }
   .badge.banned { background:rgba(239,68,68,0.15); color:var(--red);
     border:1px solid rgba(239,68,68,0.3); }
   .badge.ok     { background:rgba(34,197,94,0.12); color:var(--green);
     border:1px solid rgba(34,197,94,0.25); }
   .badge.perm   { background:rgba(168,85,247,0.15); color:var(--purple);
     border:1px solid rgba(168,85,247,0.3); }
   /* Ban timer */
   .ban-timer { font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:var(--amber); }
   /* Empty state */
   .empty { text-align:center; padding:40px; color:var(--muted); font-size:0.85rem; }
   .empty-icon { font-size:2.5rem; margin-bottom:10px; opacity:0.4; }
   /* Baseline info */
   .baseline-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; }
   .bl-card { background:var(--surface2); border:1px solid var(--border); border-radius:8px; padding:14px; }
   .bl-label { font-size:0.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.06em; }
   .bl-value { font-size:1.3rem; font-weight:700; font-family:'JetBrains Mono',monospace;
     color:var(--teal); margin-top:4px; }
   /* Footer */
   .footer { text-align:center; padding:20px; color:var(--muted); font-size:0.75rem;
     border-top:1px solid var(--border); margin-top:8px; }
   /* Rank number */
   .rank { width:24px; height:24px; border-radius:6px; background:var(--surface2);
     display:inline-flex; align-items:center; justify-content:center;
     font-size:0.72rem; font-weight:700; color:var(--muted); }
   .rank.r1 { background:rgba(245,158,11,0.2); color:var(--amber); }
   .rank.r2 { background:rgba(156,163,175,0.2); color:#9ca3af; }
   .rank.r3 { background:rgba(180,83,9,0.2); color:#92400e; }
</style>
</head>
<body>
<div class="topbar">
   <div class="logo">
     <div class="logo-icon">🛡</div>
     <div>
       <div class="logo-text">HNG Anomaly Detector</div>
       <div class="logo-sub">Real-Time HTTP Traffic Monitor</div>
     </div>
   </div>
   <div class="topbar-right">
     <div class="live-badge"><div class="pulse"></div>LIVE</div>
     <div class="uptime-text">Up: {{ uptime }} &nbsp;|&nbsp; {{ now_utc }}</div>
   </div>
</div>
 
<!-- Stat cards -->
<div class="cards">
   <div class="card {{ 'danger' if m.global_rps > m.mean * 3 else 'success' }}">
     <div class="card-icon">⚡</div>
     <div class="card-label">Global req/s</div>
     <div class="card-value {{ 'bad' if m.global_rps > m.mean * 3 else 'good' }}">{{  '%.2f'|format(m.global_rps) }}</div>
     <div class="card-sub">Sliding 60-second window</div>
   </div>
   <div class="card {{ 'danger' if m.banned_count > 0 else 'success' }}">
     <div class="card-icon">🚫</div>
     <div class="card-label">Banned IPs</div>
     <div class="card-value {{ 'bad' if m.banned_count > 0 else 'good' }}">{{ m.banned_count }}</div>
     <div class="card-sub">Active iptables DROP rules</div>
   </div>
   <div class="card">
     <div class="card-icon">📊</div>
     <div class="card-label">Baseline Mean</div>
     <div class="card-value info">{{  '%.3f'|format(m.mean) }}</div>
     <div class="card-sub">±{{  '%.3f'|format(m.stddev) }} σ &nbsp;({{ m.source }})</div>
   </div>
   <div class="card {{ 'warn' if m.cpu > 70 else 'success' }}">
     <div class="card-icon">💻</div>
     <div class="card-label">CPU Usage</div>
     <div class="card-value {{ 'bad' if m.cpu > 80 else 'warn' if m.cpu > 60 else 'good' }}">{{ m.cpu }}%</div>
     <div class="progress-bar"><div class="progress-fill {{ 'fill-red' if m.cpu>80 else 'fill-amber' if m.cpu>60 else 'fill-green' }}"  style="width:{{ m.cpu }}%"></div></div>
   </div>
   <div class="card {{ 'warn' if m.mem > 70 else 'success' }}">
     <div class="card-icon">🧠</div>
     <div class="card-label">Memory Usage</div>
     <div class="card-value {{ 'bad' if m.mem > 80 else 'warn' if m.mem > 60 else 'good' }}">{{ m.mem }}%</div>
     <div class="progress-bar"><div class="progress-fill {{ 'fill-red' if m.mem>80 else 'fill-amber' if m.mem>60 else 'fill-green' }}"  style="width:{{ m.mem }}%"></div></div>
     <div class="card-sub">{{ m.mem_used_mb }} / {{ m.mem_total_mb }} MB</div>
   </div>
   <div class="card">
     <div class="card-icon">🔬</div>
     <div class="card-label">Baseline Samples</div>
     <div class="card-value info">{{ m.sample_count }}</div>
     <div class="card-sub">30-min rolling window</div>
   </div>
</div>
 
<!-- Baseline detail -->
<div class="section">
   <div class="section-header">
     <span class="section-title">📈 Baseline Statistics</span>
     <span class="section-badge">Recalculated every 60s — Source: {{ m.source }}</span>
   </div>
   <div class="baseline-grid">
     <div class="bl-card"><div class="bl-label">Effective Mean</div><div class="bl-value">{{  '%.4f'|format(m.mean) }} req/s</div></div>
     <div class="bl-card"><div class="bl-label">Std Deviation</div><div class="bl-value">{{  '%.4f'|format(m.stddev) }}</div></div>
     <div class="bl-card"><div class="bl-label">Error Rate Mean</div><div class="bl-value">{{  '%.4f'|format(m.error_mean) }} req/s</div></div>
     <div class="bl-card"><div class="bl-label">Error Rate Std</div><div class="bl-value">{{  '%.4f'|format(m.error_stddev) }}</div></div>
     <div class="bl-card"><div class="bl-label">Last Recalc</div><div class="bl-value"  style="font-size:0.9rem">{{ m.last_recalc_str }}</div></div>
     <div class="bl-card"><div class="bl-label">Z Threshold</div><div class="bl-value">3.0</div></div>
   </div>
</div>
 
<!-- Banned IPs -->
<div class="section">
   <div class="section-header">
     <span class="section-title">🚫 Currently Banned IPs</span>
     <span class="section-badge">{{ m.banned_count }} active</span>
   </div>
   {% if m.bans %}
   <table class="data-table">
     <thead><tr><th>IP Address</th><th>Banned At</th><th>Duration</th><th>Remaining</th><th>Offences</th><th>Condition</th><th>Rate</th></tr></thead>
     <tbody>
     {% for b in m.bans %}
     <tr>
       <td><code>{{ b.ip }}</code></td>
       <td style="color:var(--muted);font-size:0.78rem">{{ b.banned_at_str }}</td>
       <td>{% if b.permanent %}<span class="badge perm">♾ PERMANENT</span>{% else %}{{ b.duration_str }}{% endif %}</td>
       <td><span class="ban-timer">{% if b.permanent %}∞{% else %}{{ b.remaining_str }}{% endif %}</span></td>
       <td><span class="badge {{ 'perm' if b.offence_count >= 4 else 'banned' }}">{{ b.offence_count }}</span></td>
       <td style="font-size:0.76rem;max-width:280px;word-break:break-word;color:var(--muted)">{{ b.condition }}</td>
       <td style="font-family:'JetBrains Mono',monospace;color:var(--red)">{{  '%.2f'|format(b.rate) }}/s</td>
     </tr>
     {% endfor %}
     </tbody>
   </table>
   {% else %}
   <div class="empty"><div class="empty-icon">✅</div>No IPs currently banned — system is healthy</div>
   {% endif %}
</div>
 
<!-- Top IPs -->
<div class="section">
   <div class="section-header">
     <span class="section-title">📡 Top {{ m.top_ips|length }} Source IPs</span>
     <span class="section-badge">By total request count</span>
   </div>
   {% if m.top_ips %}
   <table class="data-table">
     <thead><tr><th>#</th><th>IP Address</th><th>Requests</th><th>Status</th><th>Bar</th></tr></thead>
     <tbody>
     {% set max_req = m.top_ips[0][1] if m.top_ips else 1 %}
     {% for ip, count in m.top_ips %}
     <tr>
       <td><span class="rank {{ 'r1' if loop.index==1 else 'r2' if loop.index==2 else 'r3' if loop.index==3 else '' }}">{{ loop.index }}</span></td>
       <td><code>{{ ip }}</code></td>
       <td style="font-family:'JetBrains Mono',monospace;font-weight:600">{{ count }}</td>
       <td>{% if ip in m.banned_ips_set %}<span class="badge banned">● BANNED</span>{% else %}<span class="badge ok">● OK</span>{% endif %}</td>
       <td style="width:200px"><div class="progress-bar"  style="margin-top:0"><div class="progress-fill {{ 'fill-red' if ip in m.banned_ips_set else 'fill-green' }}"  style="width:{{ [(count * 100 // max_req), 100]|min }}%"></div></div></td>
     </tr>
     {% endfor %}
     </tbody>
   </table>
   {% else %}
   <div class="empty"><div class="empty-icon">📭</div>No traffic recorded yet — waiting for requests</div>
   {% endif %}
</div>
 
<div class="footer">
   HNG Stage 4 — Anomaly Detection Engine &nbsp;|&nbsp;
   Auto-refreshes every {{ refresh }}s &nbsp;|&nbsp;
   Baseline last recalculated: {{ m.last_recalc_str }}
</div>
<script>
  // Auto-refresh with smooth countdown indicator in title
   let countdown = {{ refresh }};
   setInterval(() => {
     countdown--;
     document.title =  `[${countdown}s] HNG Anomaly Detector`;
     if (countdown <= 0) { countdown = {{ refresh }}; location.reload(); }
   }, 1000);
</script>
</body></html>
 '''
 
class Dashboard:
     def __init__(self, config: Config, baseline, blocker, detector):
         self.config = config
         self.baseline = baseline
         self.blocker = blocker
         self.detector = detector
         self._start_time = time.time()
         self.app = Flask(__name__)
         self.app.logger.disabled = True
         self.app.add_url_rule('/',  'index', self._index)
         self.app.add_url_rule('/api/metrics',  'api', self._api)
         self.app.add_url_rule('/health',  'health', self._health)
 
     def start(self):
         host = self.config.dashboard.host
         port = self.config.dashboard.port
         threading.Thread(
             target=lambda: self.app.run(host=host, port=port, debug=False, use_reloader=False),
             name='Dashboard', daemon=True).start()
         print(f'[Dashboard] Live at http://{host}:{port}/')
 
     def _build(self) -> dict:
         now = time.time()
         snap = self.baseline.get_snapshot()
         bans = self.blocker.get_active_bans()
         top_ips = self.detector.get_top_ips(self.config.dashboard.top_ips_count)
         cpu = psutil.cpu_percent(interval=None)
         mem = psutil.virtual_memory()
         ban_data = []
         for b in bans:
             elapsed = now - b.banned_at
             if b.duration_seconds is None:
                 remaining_str =  'permanent'; permanent = True
                 duration_str =  'permanent' 
             else:
                 remaining = max(0, b.duration_seconds - elapsed)
                 remaining_str = self._human(int(remaining))
                 permanent = False
                 duration_str = self._human(b.duration_seconds)
             ban_data.append({'ip':b.ip,  'banned_at_str':self._fmt(b.banned_at),
                  'duration_str':duration_str,  'remaining_str':remaining_str,
                  'permanent':permanent,  'condition':b.condition,
                  'rate':b.rate,  'offence_count':b.offence_count})
         return {'global_rps':self.detector.get_global_rate(),
                  'banned_count':len(bans),  'bans':ban_data,
                  'banned_ips_set':{b.ip for b in bans},
                  'top_ips':top_ips,  'mean':snap.mean,  'stddev':snap.stddev,
                  'error_mean':snap.error_mean,  'error_stddev':snap.error_stddev,
                  'sample_count':snap.sample_count,  'source':snap.source,
                  'last_recalc_str':self._fmt(snap.last_recalc),
                  'cpu':round(cpu,1),  'mem':round(mem.percent,1),
                  'mem_used_mb':round(mem.used/1024/1024),
                  'mem_total_mb':round(mem.total/1024/1024)}
 
     def _index(self):
         m = self._build()
         uptime = self._human(int(time.time() - self._start_time))
         now_utc = self._fmt(time.time())
         refresh = self.config.dashboard.refresh_interval_seconds
         return render_template_string(DASHBOARD_HTML, m=m, uptime=uptime, now_utc=now_utc, refresh=refresh)
 
     def _api(self):
         m = self._build()
         m['banned_ips_set'] = list(m['banned_ips_set'])
         return jsonify(m)
 
     def _health(self): return jsonify({'status':'ok','uptime':time.time()-self._start_time})
 
     @staticmethod
     def _human(s):
         if s < 60: return f'{s}s' 
         if s < 3600: m,sec=divmod(s,60); return f'{m}m {sec}s' 
         h,r=divmod(s,3600); return f'{h}h {r//60}m' 
 
     @staticmethod
     def _fmt(ts):
         import datetime
         return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
