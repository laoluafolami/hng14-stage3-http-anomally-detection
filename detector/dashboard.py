import os, threading, time
import psutil
from flask import Flask, jsonify, render_template_string
from config import Config
 
# ── Full HTML dashboard with stunning design ─────────────────────────────
DASHBOARD_HTML =  '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"  content="width=device-width, initial-scale=1.0">
<title>HNG Anomaly Detector</title>
<style>
   @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');
   :root {
     --bg-deep: #050811;
     --bg-mid: #0a0f1e;
     --surface: rgba(15, 23, 42, 0.6);
     --surface2: rgba(30, 41, 59, 0.4);
     --border: rgba(100, 116, 139, 0.3);
     --text: #f1f5f9;
     --muted: #94a3b8;
     --cyan: #06b6d4;
     --cyan-glow: rgba(6, 182, 212, 0.4);
     --magenta: #ec4899;
     --magenta-glow: rgba(236, 72, 153, 0.4);
     --emerald: #10b981;
     --emerald-glow: rgba(16, 185, 129, 0.4);
     --amber: #f59e0b;
     --amber-glow: rgba(245, 158, 11, 0.4);
     --red: #ef4444;
     --red-glow: rgba(239, 68, 68, 0.4);
     --violet: #8b5cf6;
     --violet-glow: rgba(139, 92, 246, 0.4);
     --orange: #f97316;
     --orange-glow: rgba(249, 115, 22, 0.4);
     --lime: #84cc16;
     --lime-glow: rgba(132, 204, 22, 0.4);
   }
   * { box-sizing:border-box; margin:0; padding:0; }
   
   @keyframes gradientShift {
     0% { background-position: 0% 50%; }
     50% { background-position: 100% 50%; }
     100% { background-position: 0% 50%; }
   }
   
   @keyframes float {
     0%, 100% { transform: translateY(0px); }
     50% { transform: translateY(-20px); }
   }
   
   @keyframes pulse { 
     0%, 100% { opacity:1; transform:scale(1); } 
     50% { opacity:0.6; transform:scale(1.4); } 
   }
   
   @keyframes shimmer {
     0% { background-position: -1000px 0; }
     100% { background-position: 1000px 0; }
   }
   
   @keyframes glow {
     0%, 100% { filter: brightness(1) drop-shadow(0 0 8px currentColor); }
     50% { filter: brightness(1.3) drop-shadow(0 0 20px currentColor); }
   }
   
   @keyframes slideInUp {
     from { opacity: 0; transform: translateY(30px); }
     to { opacity: 1; transform: translateY(0); }
   }
   
   @keyframes rotateGlow {
     0% { transform: rotate(0deg); }
     100% { transform: rotate(360deg); }
   }
   
   body { 
     background: linear-gradient(135deg, #050811 0%, #0d1426 25%, #1a0b2e 50%, #0d1426 75%, #050811 100%);
     background-size: 400% 400%;
     animation: gradientShift 15s ease infinite;
     color: var(--text); 
     font-family: 'Rajdhani', sans-serif;
     min-height: 100vh;
     position: relative;
     overflow-x: hidden;
   }
   
   body::before {
     content: '';
     position: fixed;
     top: 0; left: 0; right: 0; bottom: 0;
     background: 
       radial-gradient(circle at 20% 30%, rgba(6, 182, 212, 0.08) 0%, transparent 50%),
       radial-gradient(circle at 80% 70%, rgba(236, 72, 153, 0.08) 0%, transparent 50%),
       radial-gradient(circle at 40% 80%, rgba(139, 92, 246, 0.06) 0%, transparent 50%);
     pointer-events: none;
     z-index: 0;
   }
   
   body::after {
     content: '';
     position: fixed;
     top: 0; left: 0; right: 0; bottom: 0;
     background-image: 
       repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.01) 2px, rgba(255,255,255,0.01) 4px);
     pointer-events: none;
     z-index: 1;
   }
   
   .topbar { 
     background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
     backdrop-filter: blur(20px) saturate(180%);
     border-bottom: 2px solid rgba(6, 182, 212, 0.3);
     padding: 18px 28px;
     display: flex; 
     justify-content: space-between; 
     align-items: center;
     position: sticky; 
     top: 0; 
     z-index: 100;
     box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
     animation: slideInUp 0.6s ease-out;
   }
   
   .logo { display: flex; align-items: center; gap: 14px; }
   
   .logo-icon { 
     width: 44px; 
     height: 44px; 
     background: linear-gradient(135deg, var(--cyan) 0%, var(--magenta) 100%);
     border-radius: 12px; 
     display: flex; 
     align-items: center; 
     justify-content: center;
     font-size: 22px; 
     box-shadow: 0 0 30px var(--cyan-glow), 0 0 60px var(--magenta-glow);
     animation: glow 2s ease-in-out infinite;
     position: relative;
   }
   
   .logo-icon::before {
     content: '';
     position: absolute;
     inset: -3px;
     background: linear-gradient(45deg, var(--cyan), var(--magenta), var(--violet), var(--cyan));
     background-size: 300% 300%;
     border-radius: 14px;
     z-index: -1;
     opacity: 0.4;
     animation: gradientShift 3s ease infinite;
   }
   
   .logo-text { 
     font-size: 1.4rem; 
     font-weight: 900; 
     font-family: 'Orbitron', sans-serif;
     background: linear-gradient(135deg, var(--cyan) 0%, var(--magenta) 50%, var(--violet) 100%);
     -webkit-background-clip: text;
     -webkit-text-fill-color: transparent;
     background-clip: text;
     letter-spacing: 1px;
   }
   
   .logo-sub { 
     font-size: 0.75rem; 
     color: var(--muted); 
     font-weight: 400; 
     letter-spacing: 2px;
     text-transform: uppercase;
   }
   
   .topbar-right { display: flex; align-items: center; gap: 24px; }
   
   .live-badge { 
     display: flex; 
     align-items: center; 
     gap: 8px; 
     background: rgba(16, 185, 129, 0.15);
     border: 2px solid rgba(16, 185, 129, 0.4); 
     border-radius: 25px; 
     padding: 6px 16px; 
     font-size: 0.8rem; 
     font-weight: 700;
     color: var(--emerald);
     box-shadow: 0 0 20px var(--emerald-glow);
     text-transform: uppercase;
     letter-spacing: 1.5px;
   }
   
   .pulse { 
     width: 10px; 
     height: 10px; 
     background: var(--emerald); 
     border-radius: 50%;
     animation: pulse 1.5s infinite;
     box-shadow: 0 0 10px var(--emerald);
   }
   
   .uptime-text { 
     font-size: 0.85rem; 
     color: var(--muted); 
     font-family: 'Fira Code', monospace; 
     font-weight: 500;
   }
   
   .cards { 
     display: grid; 
     grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
     gap: 20px; 
     padding: 32px 28px;
     position: relative;
     z-index: 2;
   }
   
   .card { 
     background: var(--surface);
     backdrop-filter: blur(20px) saturate(180%);
     border: 1px solid var(--border); 
     border-radius: 16px;
     padding: 24px; 
     position: relative; 
     overflow: hidden; 
     transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
     animation: slideInUp 0.8s ease-out backwards;
   }
   
   .card:nth-child(1) { animation-delay: 0.1s; }
   .card:nth-child(2) { animation-delay: 0.2s; }
   .card:nth-child(3) { animation-delay: 0.3s; }
   .card:nth-child(4) { animation-delay: 0.4s; }
   .card:nth-child(5) { animation-delay: 0.5s; }
   .card:nth-child(6) { animation-delay: 0.6s; }
   
   .card::before { 
     content: ''; 
     position: absolute; 
     top: 0; 
     left: 0; 
     right: 0; 
     height: 4px;
   }
   
   .card:nth-child(1)::before { 
     background: linear-gradient(90deg, var(--cyan), var(--violet));
     box-shadow: 0 0 20px var(--cyan-glow);
   }
   
   .card:nth-child(2)::before { 
     background: linear-gradient(90deg, var(--magenta), var(--orange));
     box-shadow: 0 0 20px var(--magenta-glow);
   }
   
   .card:nth-child(3)::before { 
     background: linear-gradient(90deg, var(--violet), var(--magenta));
     box-shadow: 0 0 20px var(--violet-glow);
   }
   
   .card:nth-child(4)::before { 
     background: linear-gradient(90deg, var(--amber), var(--orange));
     box-shadow: 0 0 20px var(--amber-glow);
   }
   
   .card:nth-child(5)::before { 
     background: linear-gradient(90deg, var(--emerald), var(--lime));
     box-shadow: 0 0 20px var(--emerald-glow);
   }
   
   .card:nth-child(6)::before { 
     background: linear-gradient(90deg, var(--lime), var(--emerald));
     box-shadow: 0 0 20px var(--lime-glow);
   }
   
   .card::after {
     content: '';
     position: absolute;
     inset: 0;
     background: radial-gradient(circle at var(--x, 50%) var(--y, 50%), rgba(255,255,255,0.08) 0%, transparent 60%);
     opacity: 0;
     transition: opacity 0.4s;
     pointer-events: none;
   }
   
   .card:hover {
     transform: translateY(-8px) scale(1.02);
     box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
     border-color: rgba(255, 255, 255, 0.2);
   }
   
   .card:hover::after { opacity: 1; }
   
   .card.danger::before { 
     background: linear-gradient(90deg, var(--red), var(--orange));
     box-shadow: 0 0 25px var(--red-glow);
   }
   
   .card.success::before { 
     background: linear-gradient(90deg, var(--emerald), var(--lime));
     box-shadow: 0 0 25px var(--emerald-glow);
   }
   
   .card.warn::before { 
     background: linear-gradient(90deg, var(--amber), var(--red));
     box-shadow: 0 0 25px var(--amber-glow);
   }
   
   .card-label { 
     font-size: 0.75rem; 
     color: var(--muted); 
     text-transform: uppercase;
     letter-spacing: 1.5px; 
     font-weight: 600;
     font-family: 'Orbitron', sans-serif;
   }
   
   .card-value { 
     font-size: 2.8rem; 
     font-weight: 900; 
     margin: 12px 0 6px;
     font-family: 'Orbitron', monospace; 
     line-height: 1;
     letter-spacing: -1px;
   }
   
   .card-value.good { 
     color: var(--emerald);
     text-shadow: 0 0 20px var(--emerald-glow);
   }
   
   .card-value.bad { 
     color: var(--red); 
     text-shadow: 0 0 25px var(--red-glow);
     animation: glow 1.5s ease-in-out infinite;
   }
   
   .card-value.warn { 
     color: var(--amber);
     text-shadow: 0 0 20px var(--amber-glow);
   }
   
   .card-value.info { 
     color: var(--cyan);
     text-shadow: 0 0 20px var(--cyan-glow);
   }
   
   .card-sub { 
     font-size: 0.78rem; 
     color: var(--muted);
     font-weight: 400;
   }
   
   .card-icon { 
     position: absolute; 
     top: 20px; 
     right: 20px; 
     font-size: 2.2rem; 
     opacity: 0.12;
     animation: float 3s ease-in-out infinite;
   }
   
   .progress-bar { 
     height: 8px; 
     background: rgba(100, 116, 139, 0.2); 
     border-radius: 4px; 
     margin-top: 10px;
     overflow: hidden;
     position: relative;
   }
   
   .progress-bar::before {
     content: '';
     position: absolute;
     top: 0;
     left: -100%;
     width: 100%;
     height: 100%;
     background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
     animation: shimmer 2s infinite;
   }
   
   .progress-fill { 
     height: 100%; 
     border-radius: 4px; 
     transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
     position: relative;
     overflow: hidden;
   }
   
   .fill-green { 
     background: linear-gradient(90deg, var(--emerald), var(--lime));
     box-shadow: 0 0 15px var(--emerald-glow);
   }
   
   .fill-amber { 
     background: linear-gradient(90deg, var(--amber), var(--orange));
     box-shadow: 0 0 15px var(--amber-glow);
   }
   
   .fill-red { 
     background: linear-gradient(90deg, var(--red), var(--magenta));
     box-shadow: 0 0 15px var(--red-glow);
   }
   
   .section { 
     padding: 0 28px 28px;
     position: relative;
     z-index: 2;
     animation: slideInUp 1s ease-out backwards;
   }
   
   .section:nth-of-type(2) { animation-delay: 0.7s; }
   .section:nth-of-type(3) { animation-delay: 0.8s; }
   .section:nth-of-type(4) { animation-delay: 0.9s; }
   
   .section-header { 
     display: flex; 
     justify-content: space-between; 
     align-items: center;
     padding: 16px 0; 
     border-bottom: 2px solid var(--border); 
     margin-bottom: 20px;
   }
   
   .section-title { 
     font-size: 1rem; 
     font-weight: 700; 
     font-family: 'Orbitron', sans-serif;
     color: var(--text);
     letter-spacing: 1px;
     text-transform: uppercase;
   }
   
   .section-badge { 
     background: var(--surface2);
     backdrop-filter: blur(10px);
     border: 1px solid var(--border);
     border-radius: 25px; 
     padding: 5px 14px; 
     font-size: 0.75rem; 
     color: var(--muted);
     font-weight: 600;
   }
   
   .data-table { 
     width: 100%; 
     border-collapse: collapse; 
     font-size: 0.85rem;
     background: var(--surface);
     backdrop-filter: blur(20px);
     border-radius: 12px;
     overflow: hidden;
   }
   
   .data-table th { 
     text-align: left; 
     padding: 14px 16px; 
     color: var(--muted);
     font-weight: 700; 
     background: rgba(30, 41, 59, 0.6);
     font-size: 0.75rem;
     text-transform: uppercase; 
     letter-spacing: 1.2px;
     font-family: 'Orbitron', sans-serif;
   }
   
   .data-table td { 
     padding: 14px 16px; 
     border-bottom: 1px solid rgba(100, 116, 139, 0.2);
   }
   
   .data-table tr { transition: all 0.3s ease; }
   
   .data-table tr:hover td { 
     background: rgba(6, 182, 212, 0.05);
     transform: scale(1.01);
   }
   
   .data-table tr:last-child td { border-bottom: none; }
   
   code { 
     font-family: 'Fira Code', monospace; 
     font-size: 0.85em;
     background: rgba(6, 182, 212, 0.12); 
     border: 1px solid rgba(6, 182, 212, 0.3);
     border-radius: 6px; 
     padding: 3px 8px; 
     color: var(--cyan);
     font-weight: 600;
   }
   
   .badge { 
     display: inline-flex; 
     align-items: center; 
     gap: 6px; 
     padding: 4px 12px;
     border-radius: 25px; 
     font-size: 0.72rem; 
     font-weight: 700;
     text-transform: uppercase;
     letter-spacing: 0.5px;
   }
   
   .badge.banned { 
     background: rgba(239, 68, 68, 0.2); 
     color: var(--red);
     border: 1px solid rgba(239, 68, 68, 0.4);
     box-shadow: 0 0 15px var(--red-glow);
   }
   
   .badge.ok { 
     background: rgba(16, 185, 129, 0.15); 
     color: var(--emerald);
     border: 1px solid rgba(16, 185, 129, 0.3);
     box-shadow: 0 0 12px var(--emerald-glow);
   }
   
   .badge.perm { 
     background: rgba(139, 92, 246, 0.2); 
     color: var(--violet);
     border: 1px solid rgba(139, 92, 246, 0.4);
     box-shadow: 0 0 15px var(--violet-glow);
   }
   
   .ban-timer { 
     font-family: 'Fira Code', monospace; 
     font-size: 0.85rem; 
     color: var(--amber);
     font-weight: 600;
   }
   
   .empty { 
     text-align: center; 
     padding: 50px; 
     color: var(--muted); 
     font-size: 0.9rem;
   }
   
   .empty-icon { 
     font-size: 3rem; 
     margin-bottom: 12px; 
     opacity: 0.3;
     animation: float 3s ease-in-out infinite;
   }
   
   .baseline-grid { 
     display: grid; 
     grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
     gap: 16px;
   }
   
   .bl-card { 
     background: var(--surface2);
     backdrop-filter: blur(15px);
     border: 1px solid var(--border); 
     border-radius: 12px; 
     padding: 18px;
     transition: all 0.3s ease;
   }
   
   .bl-card:hover {
     transform: translateY(-4px);
     border-color: rgba(6, 182, 212, 0.4);
     box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
   }
   
   .bl-label { 
     font-size: 0.72rem; 
     color: var(--muted); 
     text-transform: uppercase; 
     letter-spacing: 1.2px;
     font-weight: 600;
     font-family: 'Orbitron', sans-serif;
   }
   
   .bl-value { 
     font-size: 1.5rem; 
     font-weight: 900; 
     font-family: 'Orbitron', monospace;
     color: var(--cyan);
     text-shadow: 0 0 15px var(--cyan-glow);
     margin-top: 6px;
   }
   
   .footer { 
     text-align: center; 
     padding: 28px; 
     color: var(--muted); 
     font-size: 0.8rem;
     border-top: 2px solid var(--border); 
     margin-top: 20px;
     background: rgba(5, 8, 17, 0.6);
     backdrop-filter: blur(10px);
     font-weight: 500;
     letter-spacing: 0.5px;
   }
   
   .footer strong {
     color: var(--cyan);
     font-weight: 700;
   }
   
   .rank { 
     width: 28px; 
     height: 28px; 
     border-radius: 8px; 
     background: var(--surface2);
     display: inline-flex; 
     align-items: center; 
     justify-content: center;
     font-size: 0.75rem; 
     font-weight: 900; 
     color: var(--muted);
     font-family: 'Orbitron', sans-serif;
   }
   
   .rank.r1 { 
     background: linear-gradient(135deg, var(--amber), var(--orange));
     color: #fff;
     box-shadow: 0 0 20px var(--amber-glow);
   }
   
   .rank.r2 { 
     background: linear-gradient(135deg, #94a3b8, #cbd5e1);
     color: #1e293b;
     box-shadow: 0 0 15px rgba(148, 163, 184, 0.4);
   }
   
   .rank.r3 { 
     background: linear-gradient(135deg, #92400e, #b45309);
     color: #fff;
     box-shadow: 0 0 15px rgba(180, 83, 9, 0.4);
   }
   
   /* Custom scrollbar for IP table */
   .ip-scroll-container {
     max-height: 280px;
     overflow-y: auto;
     border-radius: 12px;
   }
   
   .ip-scroll-container::-webkit-scrollbar {
     width: 8px;
   }
   
   .ip-scroll-container::-webkit-scrollbar-track {
     background: var(--surface2);
     border-radius: 4px;
   }
   
   .ip-scroll-container::-webkit-scrollbar-thumb {
     background: linear-gradient(180deg, var(--cyan), var(--violet));
     border-radius: 4px;
     box-shadow: 0 0 10px var(--cyan-glow);
   }
   
   .ip-scroll-container::-webkit-scrollbar-thumb:hover {
     background: linear-gradient(180deg, var(--magenta), var(--cyan));
   }
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
       <td style="font-family:'Fira Code',monospace;color:var(--red)">{{  '%.2f'|format(b.rate) }}/s</td>
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
   <div class="ip-scroll-container">
   <table class="data-table">
     <thead style="position: sticky; top: 0; z-index: 10;"><tr><th>#</th><th>IP Address</th><th>Requests</th><th>Status</th><th>Bar</th></tr></thead>
     <tbody>
     {% set max_req = m.top_ips[0][1] if m.top_ips else 1 %}
     {% for ip, count in m.top_ips %}
     <tr>
       <td><span class="rank {{ 'r1' if loop.index==1 else 'r2' if loop.index==2 else 'r3' if loop.index==3 else '' }}">{{ loop.index }}</span></td>
       <td><code>{{ ip }}</code></td>
       <td style="font-family:'Fira Code',monospace;font-weight:600">{{ count }}</td>
       <td>{% if ip in m.banned_ips_set %}<span class="badge banned">● BANNED</span>{% else %}<span class="badge ok">● OK</span>{% endif %}</td>
       <td style="width:200px"><div class="progress-bar"  style="margin-top:0"><div class="progress-fill {{ 'fill-red' if ip in m.banned_ips_set else 'fill-green' }}"  style="width:{{ [(count * 100 // max_req), 100]|min }}%"></div></div></td>
     </tr>
     {% endfor %}
     </tbody>
   </table>
   </div>
   {% else %}
   <div class="empty"><div class="empty-icon">📭</div>No traffic recorded yet — waiting for requests</div>
   {% endif %}
</div>
 
<div class="footer">
   HNG Stage 3 — Anomaly Detection Engine &nbsp;•&nbsp; Auto-refreshes every {{ refresh }}s &nbsp;|&nbsp; Built by <strong>Olaoluwa Afolami</strong> | <span id="currentYear">2026</span>
</div>
<script>
  // Track mouse position for card hover effects
  document.addEventListener('mousemove', (e) => {
    document.querySelectorAll('.card').forEach(card => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      card.style.setProperty('--x', x + '%');
      card.style.setProperty('--y', y + '%');
    });
  });
  
  // Auto-refresh with smooth countdown indicator in title
  let countdown = {{ refresh }};
  setInterval(() => {
    countdown--;
    document.title =  `[${countdown}s] HNG Anomaly Detector`;
    if (countdown <= 0) { countdown = {{ refresh }}; location.reload(); }
  }, 1000);
  
  // Update year dynamically
  document.getElementById('currentYear').textContent = new Date().getFullYear();
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
