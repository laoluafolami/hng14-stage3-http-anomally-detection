# 🛡️ HNG Stage 3: Real-Time HTTP Anomaly Detection System

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

A production-grade, real-time anomaly detection system that monitors HTTP traffic patterns, learns baseline behavior dynamically, and automatically blocks suspicious IPs using statistical analysis and iptables rules.

## 🌐 Live Demo

- **Server IP:** `20.9.87.35`
- **Dashboard URL:** `http://20.9.87.35:8080/` or `http://hng-stage3.centralus.cloudapp.azure.com/`
- **API Endpoint:** `http://20.9.87.35:8080/api/metrics`
- **Health Check:** `http://20.9.87.35:8080/health`


<img width="1900" height="986" alt="image" src="https://github.com/user-attachments/assets/542603ca-2da3-40ce-90ee-ae0d5d9bac6c" />
> 🔴 **Note:** Dashboard and API are live 24/7.

## 📖 Blog Post

Read the comprehensive beginner-friendly guide: **[Building a Real-Time Anomaly Detection System: A Complete Guide](https://laoluafolami.hashnode.dev/building-a-real-time-anomaly-detection-system-a-complete-beginner-s-guide)**

The blog post covers:
- What anomaly detection is and why it matters
- How sliding windows track traffic in real-time
- How the system learns "normal" behavior
- The statistical logic behind threat detection
- How iptables blocks malicious IPs

---

## 🎯 What This System Does

This anomaly detection engine monitors incoming HTTP requests in real-time and identifies suspicious patterns by:

1. **Learning Normal Behavior** - Builds a statistical baseline from legitimate traffic
2. **Real-Time Monitoring** - Tracks request rates using efficient sliding windows
3. **Smart Detection** - Uses Z-score analysis to identify anomalies (3σ threshold)
4. **Automatic Mitigation** - Blocks malicious IPs using iptables with escalating ban durations
5. **Visual Monitoring** - Provides a stunning real-time dashboard for system observation

### Why This Matters

Traditional security tools often rely on signature-based detection (known attack patterns). This system uses **behavioral analysis** - it learns what's normal for *your* traffic and flags anything unusual. This catches:
- DDoS attacks (distributed denial of service)
- Brute force attempts
- Web scraping bots
- API abuse
- Zero-day attacks (unknown threats)

---

## 🏗️ Architecture & Core Concepts

### 1. **Sliding Window Mechanism**

The sliding window is the heart of our real-time monitoring. Here's how it works:

#### Data Structure: `collections.deque`

```python
from collections import deque
import time

# Create a window that holds 60 seconds of timestamps
request_window = deque(maxlen=None)  # No size limit, time-based instead

# When a request arrives
def log_request(ip_address):
    current_time = time.time()
    request_window.append((current_time, ip_address))
```

#### Why `deque`?
- **O(1) append** - Adding new requests is instantaneous
- **O(1) popleft** - Removing old requests is instantaneous
- **Memory efficient** - Only stores timestamps, not full request data
- **Thread-safe** with proper locking

#### Eviction Logic

We use **time-based eviction** rather than count-based:

```python
def clean_old_requests(window, current_time, window_size=60):
    """Remove requests older than 60 seconds"""
    while window and (current_time - window[0][0]) > window_size:
        window.popleft()  # O(1) removal from left
```

**Why time-based?**
- Traffic volume varies (100 req/min vs 10,000 req/min)
- Fixed-size windows would compare different time periods
- Time-based windows ensure consistent rate calculations

**Example Flow:**
```
Time: 10:00:00 - Window: []
Time: 10:00:01 - Request arrives → Window: [10:00:01]
Time: 10:00:02 - Request arrives → Window: [10:00:01, 10:00:02]
...
Time: 10:01:02 - Clean old data → Window: [10:00:03, 10:00:04, ..., 10:01:02]
                  (10:00:01 and 10:00:02 removed, older than 60s)
```

### 2. **Baseline Learning System**

The baseline learns what "normal" looks like for your traffic.

#### Configuration

```python
BASELINE_WINDOW_SIZE = 1800  # 30 minutes of historical data
RECALCULATION_INTERVAL = 60  # Recalculate every 60 seconds
MINIMUM_SAMPLES = 30         # Need at least 30 data points
FLOOR_VALUES = {
    'mean': 0.5,      # Minimum average requests/second
    'stddev': 0.1     # Minimum standard deviation
}
```

#### How It Works

**Step 1: Data Collection**
```python
baseline_samples = deque(maxlen=1800)  # 30 minutes of per-second rates

# Every second, calculate and store the current rate
rate = len(requests_in_last_second)
baseline_samples.append(rate)
```

**Step 2: Statistical Calculation (every 60 seconds)**
```python
import statistics

def recalculate_baseline():
    if len(baseline_samples) < MINIMUM_SAMPLES:
        return None  # Not enough data yet
    
    # Calculate mean (average requests/second)
    mean = statistics.mean(baseline_samples)
    mean = max(mean, FLOOR_VALUES['mean'])  # Apply floor
    
    # Calculate standard deviation (traffic variability)
    stddev = statistics.stdev(baseline_samples)
    stddev = max(stddev, FLOOR_VALUES['stddev'])  # Apply floor
    
    return {'mean': mean, 'stddev': stddev}
```

**Step 3: Floor Values (Preventing False Positives)**

Why floors matter:
- **Low traffic scenario:** If you get 1 request/hour, mean=0.0003, stddev=0.0001
- **Single spike:** 10 requests in one second would be a massive anomaly
- **With floors:** mean=0.5, stddev=0.1 → 10 requests needs to exceed 0.5 + (3 × 0.1) = 0.8 req/s
- **Result:** Legitimate traffic spikes don't trigger false bans

#### Adaptive Learning

The baseline adapts to traffic patterns:
- **Morning rush?** Baseline adjusts upward
- **Night time lull?** Baseline adjusts downward
- **30-minute window** balances responsiveness vs. stability

### 3. **Detection Logic: Z-Score Analysis**

We use statistical Z-score to determine if traffic is anomalous.

#### The Math

```
Z-score = (X - μ) / σ

Where:
- X = Current rate (requests/second)
- μ = Baseline mean
- σ = Baseline standard deviation
```

**Interpretation:**
- Z-score < 3: Normal traffic (within 99.7% of expected)
- Z-score ≥ 3: Anomaly detected (exceeds 3 standard deviations)

#### Example Calculation

```python
# Baseline learned from normal traffic
mean = 5.0      # Average 5 requests/second
stddev = 1.5    # Standard deviation of 1.5

# Sudden spike detected
current_rate = 15.0  # 15 requests/second

# Calculate Z-score
z_score = (current_rate - mean) / stddev
z_score = (15.0 - 5.0) / 1.5
z_score = 6.67  # 🚨 WAY above threshold of 3!

# Decision: BAN THIS IP
```

**Why 3-sigma (Z=3)?**
- Statistically, 99.7% of normal data falls within ±3σ
- Balances sensitivity vs. false positives
- Industry standard for anomaly detection

### 4. **Progressive Ban System**

IPs get escalating penalties for repeated violations:

| Offense | Duration | Condition |
|---------|----------|-----------|
| 1st     | 5 minutes | First anomaly detected |
| 2nd     | 15 minutes | Second offense within 24h |
| 3rd     | 1 hour | Third offense within 24h |
| 4th+    | **PERMANENT** | Persistent malicious actor |

**Implementation:**
```python
def calculate_ban_duration(offense_count):
    if offense_count == 1:
        return 300      # 5 minutes
    elif offense_count == 2:
        return 900      # 15 minutes
    elif offense_count == 3:
        return 3600     # 1 hour
    else:
        return None     # Permanent ban
```

### 5. **iptables Integration**

iptables is Linux's built-in firewall. We use it to drop packets from banned IPs.

#### Banning an IP

```bash
# Add a DROP rule to the INPUT chain
sudo iptables -I INPUT -s 192.168.1.100 -j DROP

# What this means:
# -I INPUT    : Insert at the top of INPUT chain (checked first)
# -s IP       : Source IP address to match
# -j DROP     : Jump to DROP target (silently discard packets)
```

**Python Implementation:**
```python
import subprocess

def ban_ip(ip_address):
    try:
        cmd = ['sudo', 'iptables', '-I', 'INPUT', '-s', ip_address, '-j', 'DROP']
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Banned {ip_address}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to ban {ip_address}: {e}")
```

#### Unbanning an IP (After Timeout)

```bash
# Remove the specific DROP rule
sudo iptables -D INPUT -s 192.168.1.100 -j DROP
```

**Python Implementation:**
```python
def unban_ip(ip_address):
    try:
        cmd = ['sudo', 'iptables', '-D', 'INPUT', '-s', ip_address, '-j', 'DROP']
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Unbanned {ip_address}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ IP {ip_address} was not banned or already removed")
```

#### How iptables Works

```
┌─────────────────────────────────────────────┐
│  Incoming Packet from 192.168.1.100        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  iptables      │
        │  INPUT chain   │
        └────────┬───────┘
                 │
         ┌───────▼────────┐
         │ Check rules    │
         │ top to bottom  │
         └───────┬────────┘
                 │
    ┌────────────▼─────────────┐
    │ Rule: -s 192.168.1.100   │
    │       -j DROP            │
    └────────────┬─────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ Packet       │
         │ DROPPED      │
         │ (discarded)  │
         └──────────────┘
```

**Benefits:**
- **Kernel-level blocking** - Happens before reaching application
- **Zero CPU overhead** - Malicious packets never processed
- **Instant effect** - Active immediately after rule insertion
- **No response sent** - Attacker sees timeout (stealth mode)

### 6. **Slack Integration for Real-Time Alerts**

Get instant notifications in your Slack workspace when anomalies are detected and IPs are banned.

#### Why Slack Integration?

- **Real-time alerts** - Know about attacks immediately, even when away from dashboard
- **Team visibility** - Security team sees all events in a shared channel
- **Audit trail** - Permanent record of all bans in Slack history
- **Mobile notifications** - Slack mobile app ensures you never miss critical alerts

#### Setup Process

**Step 1: Create Slack Incoming Webhook**

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name it "Anomaly Detector" and select your workspace
4. Navigate to "Incoming Webhooks" and activate it
5. Click "Add New Webhook to Workspace"
6. Select the channel (e.g., #security-alerts)
7. Copy the webhook URL (looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)

**Step 2: Add to Configuration**

```python
class Config:
    # ... other config ...
    
    class SlackConfig:
        enabled = True
        webhook_url = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel = '#security-alerts'
        username = 'Anomaly Detector Bot'
        icon_emoji = ':shield:'
        
        # Notification settings
        notify_on_ban = True
        notify_on_unban = True
        notify_on_error = True
        min_z_score_for_alert = 5.0  # Only alert on severe anomalies
```

#### Implementation

```python
import requests
import json

class SlackNotifier:
    def __init__(self, webhook_url, channel='#security-alerts', username='Anomaly Bot'):
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
    
    def send_ban_alert(self, ip_address, rate, z_score, offense_count, duration):
        """
        Send alert when IP is banned
        """
        # Determine severity based on Z-score
        if z_score > 10:
            severity = 'CRITICAL'
            color = '#FF0000'  # Red
            emoji = '🚨'
        elif z_score > 5:
            severity = 'HIGH'
            color = '#FFA500'  # Orange
            emoji = '⚠️'
        else:
            severity = 'MEDIUM'
            color = '#FFFF00'  # Yellow
            emoji = '⚡'
        
        # Format duration
        if duration is None:
            duration_text = 'PERMANENT'
        else:
            duration_text = self._format_duration(duration)
        
        # Create rich message
        message = {
            'channel': self.channel,
            'username': self.username,
            'icon_emoji': ':shield:',
            'attachments': [{
                'color': color,
                'title': f'{emoji} IP Address Banned - {severity} Severity',
                'fields': [
                    {
                        'title': 'IP Address',
                        'value': f'`{ip_address}`',
                        'short': True
                    },
                    {
                        'title': 'Request Rate',
                        'value': f'{rate:.2f} req/s',
                        'short': True
                    },
                    {
                        'title': 'Z-Score',
                        'value': f'{z_score:.2f}σ',
                        'short': True
                    },
                    {
                        'title': 'Offense Count',
                        'value': f'#{offense_count}',
                        'short': True
                    },
                    {
                        'title': 'Ban Duration',
                        'value': duration_text,
                        'short': True
                    },
                    {
                        'title': 'Action Taken',
                        'value': 'iptables DROP rule applied',
                        'short': True
                    }
                ],
                'footer': 'HNG Anomaly Detection System',
                'ts': int(time.time())
            }]
        }
        
        self._send(message)
    
    def send_unban_alert(self, ip_address):
        """
        Send alert when IP is unbanned
        """
        message = {
            'channel': self.channel,
            'username': self.username,
            'icon_emoji': ':shield:',
            'attachments': [{
                'color': '#00FF00',  # Green
                'title': '✅ IP Address Unbanned',
                'text': f'IP `{ip_address}` has been unbanned after timeout period.',
                'footer': 'HNG Anomaly Detection System',
                'ts': int(time.time())
            }]
        }
        
        self._send(message)
    
    def send_system_alert(self, message_text, severity='info'):
        """
        Send general system alerts
        """
        colors = {
            'info': '#0000FF',
            'warning': '#FFA500',
            'error': '#FF0000',
            'success': '#00FF00'
        }
        
        emojis = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        
        message = {
            'channel': self.channel,
            'username': self.username,
            'icon_emoji': ':shield:',
            'attachments': [{
                'color': colors.get(severity, '#808080'),
                'title': f'{emojis.get(severity, "📢")} System Alert',
                'text': message_text,
                'footer': 'HNG Anomaly Detection System',
                'ts': int(time.time())
            }]
        }
        
        self._send(message)
    
    def send_daily_summary(self, stats):
        """
        Send daily summary of system activity
        """
        message = {
            'channel': self.channel,
            'username': self.username,
            'icon_emoji': ':shield:',
            'attachments': [{
                'color': '#36a64f',
                'title': '📊 Daily Security Summary',
                'fields': [
                    {
                        'title': 'Total Requests',
                        'value': f'{stats["total_requests"]:,}',
                        'short': True
                    },
                    {
                        'title': 'IPs Banned',
                        'value': str(stats['ips_banned']),
                        'short': True
                    },
                    {
                        'title': 'Anomalies Detected',
                        'value': str(stats['anomalies_detected']),
                        'short': True
                    },
                    {
                        'title': 'Permanent Bans',
                        'value': str(stats['permanent_bans']),
                        'short': True
                    },
                    {
                        'title': 'Average Traffic',
                        'value': f'{stats["avg_rate"]:.2f} req/s',
                        'short': True
                    },
                    {
                        'title': 'Peak Traffic',
                        'value': f'{stats["peak_rate"]:.2f} req/s',
                        'short': True
                    }
                ],
                'footer': 'HNG Anomaly Detection System',
                'ts': int(time.time())
            }]
        }
        
        self._send(message)
    
    def _send(self, message):
        """
        Send message to Slack webhook
        """
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"❌ Slack notification failed: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send Slack notification: {e}")
    
    @staticmethod
    def _format_duration(seconds):
        """Format seconds into human-readable duration"""
        if seconds < 60:
            return f'{seconds}s'
        elif seconds < 3600:
            return f'{seconds // 60}m'
        else:
            return f'{seconds // 3600}h'

# Usage in main detection system
slack = SlackNotifier(
    webhook_url=config.slack.webhook_url,
    channel=config.slack.channel
)

# When banning an IP
def ban_ip_with_notification(ip, rate, z_score, offense_count, duration):
    # Apply ban
    blocker.ban_ip(ip, reason=f"Z-score: {z_score:.2f}", rate=rate)
    
    # Send Slack alert
    slack.send_ban_alert(ip, rate, z_score, offense_count, duration)

# System startup notification
slack.send_system_alert(
    'Anomaly Detection System started successfully',
    severity='success'
)
```

#### Example Slack Messages

**Ban Alert:**
```
🚨 IP Address Banned - CRITICAL Severity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IP Address:      192.168.1.100
Request Rate:    45.32 req/s
Z-Score:         12.45σ
Offense Count:   #1
Ban Duration:    5 minutes
Action Taken:    iptables DROP rule applied
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HNG Anomaly Detection System | 2:34 PM
```

**Unban Alert:**
```
✅ IP Address Unbanned
IP 192.168.1.100 has been unbanned after timeout period.
HNG Anomaly Detection System | 2:39 PM
```

**Daily Summary:**
```
📊 Daily Security Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Requests:       142,354
IPs Banned:           12
Anomalies Detected:   15
Permanent Bans:       2
Average Traffic:      8.45 req/s
Peak Traffic:         127.89 req/s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HNG Anomaly Detection System | 11:59 PM
```

#### Advanced Slack Features

**Thread Replies for Updates:**
```python
def send_ban_with_updates(self, ip, rate, z_score):
    # Initial message
    response = self._send_and_get_ts({
        'text': f'🚨 Banning {ip}...',
    })
    
    # Reply in thread when ban is applied
    self._send_thread_reply(response['ts'], {
        'text': f'✅ iptables rule applied successfully'
    })
```

**Interactive Buttons (Advanced):**
```python
message = {
    'text': 'IP 192.168.1.100 detected as anomaly',
    'attachments': [{
        'callback_id': 'ban_decision',
        'actions': [
            {
                'name': 'ban',
                'text': 'Ban This IP',
                'type': 'button',
                'value': '192.168.1.100'
            },
            {
                'name': 'whitelist',
                'text': 'Whitelist',
                'type': 'button',
                'value': '192.168.1.100'
            }
        ]
    }]
}
```

#### Testing Slack Integration

```python
# Test script
if __name__ == '__main__':
    slack = SlackNotifier(webhook_url='YOUR_WEBHOOK_URL')
    
    # Test ban alert
    slack.send_ban_alert(
        ip_address='192.168.1.100',
        rate=45.5,
        z_score=8.2,
        offense_count=1,
        duration=300
    )
    
    # Test unban alert
    slack.send_unban_alert('192.168.1.100')
    
    # Test system alert
    slack.send_system_alert('Test notification', severity='info')
    
    print('✅ Test notifications sent to Slack!')
```

#### Best Practices

1. **Rate Limiting**: Don't send too many messages (Slack has limits)
```python
class RateLimitedSlackNotifier(SlackNotifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_sent = {}
        self.min_interval = 5  # seconds between similar messages
    
    def send_ban_alert(self, ip_address, *args, **kwargs):
        now = time.time()
        if ip_address in self.last_sent:
            if now - self.last_sent[ip_address] < self.min_interval:
                return  # Skip, too soon
        
        super().send_ban_alert(ip_address, *args, **kwargs)
        self.last_sent[ip_address] = now
```

2. **Severity Filtering**: Only alert on important events
```python
if z_score > config.slack.min_z_score_for_alert:
    slack.send_ban_alert(...)
```

3. **Batch Notifications**: Group multiple events
```python
def send_batch_alert(self, events):
    """Send multiple bans in one message"""
    message = {
        'text': f'🚨 {len(events)} IPs banned in the last minute',
        'attachments': [{
            'text': '\n'.join([f'• {e.ip} ({e.z_score:.2f}σ)' for e in events])
        }]
    }
    self._send(message)
```

---

## 🚀 Setup Instructions

### Prerequisites

- Fresh Ubuntu 20.04/22.04 VPS
- Root or sudo access
- At least 1GB RAM
- Public IP address

### Step 1: Initial Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git iptables nginx

# Verify Python version (3.8+ required)
python3 --version
```

### Step 2: Clone Repository

```bash
# Clone the project
git clone https://github.com/YOUR_USERNAME/hng-anomaly-detector.git
cd hng-anomaly-detector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

**requirements.txt:**
```
Flask==3.0.0
psutil==5.9.6
gunicorn==21.2.0
```

### Step 4: Configure the System

```bash
# Copy example config
cp config.example.py config.py

# Edit configuration
nano config.py
```

**config.py template:**
```python
class Config:
    # Server settings
    LOG_FILE = '/var/log/nginx/access.log'
    
    # Detection thresholds
    WINDOW_SIZE_SECONDS = 60
    Z_SCORE_THRESHOLD = 3.0
    
    # Baseline settings
    BASELINE_WINDOW_SIZE = 1800  # 30 minutes
    RECALCULATION_INTERVAL = 60   # 1 minute
    MINIMUM_SAMPLES = 30
    
    # Floor values
    FLOOR_MEAN = 0.5
    FLOOR_STDDEV = 0.1
    
    # Ban durations (seconds)
    BAN_DURATION_1ST = 300      # 5 minutes
    BAN_DURATION_2ND = 900      # 15 minutes
    BAN_DURATION_3RD = 3600     # 1 hour
    # 4th offense = permanent
    
    class DashboardConfig:
        host = '0.0.0.0'
        port = 8080
        refresh_interval_seconds = 10
        top_ips_count = 10
```

### Step 5: Configure Nginx (Log Source)

```bash
# Edit Nginx config to ensure access logs are enabled
sudo nano /etc/nginx/sites-available/default
```

Add/verify this section:
```nginx
access_log /var/log/nginx/access.log;
```

Restart Nginx:
```bash
sudo systemctl restart nginx
```

### Step 6: Set Up Sudo Permissions (for iptables)

```bash
# Allow the application to run iptables without password
sudo visudo
```

Add this line (replace `username` with your actual username):
```
username ALL=(ALL) NOPASSWD: /usr/sbin/iptables
```

### Step 7: Run the Application

#### Option A: Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python3 main.py
```

#### Option B: Production Mode (with systemd)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/anomaly-detector.service
```

Add this configuration:
```ini
[Unit]
Description=HNG Anomaly Detection System
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/hng-anomaly-detector
Environment="PATH=/path/to/hng-anomaly-detector/venv/bin"
ExecStart=/path/to/hng-anomaly-detector/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable anomaly-detector
sudo systemctl start anomaly-detector

# Check status
sudo systemctl status anomaly-detector
```

### Step 8: Configure Firewall

```bash
# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp

# Allow dashboard port
sudo ufw allow 8080/tcp

# Allow HTTP/HTTPS if using Nginx reverse proxy
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### Step 9: Verify Installation

```bash
# Check if application is running
ps aux | grep python

# Check dashboard accessibility
curl http://localhost:8080/health

# Check logs
tail -f /var/log/nginx/access.log

# View iptables rules
sudo iptables -L -n -v
```

### Step 10: Access Dashboard

Open your browser and navigate to:
```
http://YOUR_SERVER_IP:8080
```

You should see the stunning dashboard with real-time metrics! 🎉

---

## 📸 Screenshots

### Dashboard Overview
<img width="1910" height="790" alt="image" src="https://github.com/user-attachments/assets/e1be9ef7-2972-4ab1-88a9-fa3b47cc64cf" />
*Real-time monitoring dashboard showing all key metrics*

### Banned IPs Section
<img width="1900" height="986" alt="image" src="https://github.com/user-attachments/assets/e6cf3577-8bbd-4cfa-9dc8-f465c2d454e7" />
*Active bans with countdown timers and offense tracking*

### Top IPs Analysis
<img width="1874" height="335" alt="image" src="https://github.com/user-attachments/assets/af7d6666-c111-44b1-b121-b9a89bcaa8f1" />
*Top 4 IPs by request volume with visual indicators*

### Baseline Statistics
<img width="1886" height="209" alt="image" src="https://github.com/user-attachments/assets/d6acba8b-abb7-4c03-b66a-04ed6539148f" />

<img width="1782" height="859" alt="image" src="https://github.com/user-attachments/assets/23fcd2bf-6686-4531-80ad-189b2e8c96c5" />
*Statistical baseline showing mean, standard deviation, and thresholds*

### Alert State
<img width="1900" height="986" alt="image" src="https://github.com/user-attachments/assets/c1997041-e339-4591-996e-5543b686f9a0" />
*Dashboard during active anomaly detection*

---

## 🧪 Testing the System

### Generate Normal Traffic
```bash
# Light load (normal)
ab -n 1000 -c 10 http://YOUR_SERVER_IP/
```

### Trigger Detection
```bash
# Heavy load (anomaly)
ab -n 5000 -c 100 http://YOUR_SERVER_IP/
```

### Verify Ban
```bash
# Check iptables rules
sudo iptables -L -n | grep YOUR_IP

# Test from banned IP (should timeout)
curl http://YOUR_SERVER_IP/
```

---

## 📊 API Endpoints

### GET `/`
Dashboard HTML interface

### GET `/api/metrics`
Returns JSON with all metrics:
```json
{
  "global_rps": 12.5,
  "banned_count": 2,
  "bans": [...],
  "top_ips": [...],
  "mean": 5.2,
  "stddev": 1.8,
  "cpu": 23.5,
  "mem": 45.2
}
```

### GET `/health`
Health check endpoint:
```json
{
  "status": "ok",
  "uptime": 3600
}
```

---

## 🏆 Technical Highlights

### Performance Optimizations
- **O(1) insertions/deletions** with deque data structure
- **Minimal memory footprint** - only stores timestamps
- **Efficient log parsing** using real-time file monitoring
- **Kernel-level blocking** via iptables (zero application overhead)

### Security Features
- **Statistical anomaly detection** (not signature-based)
- **Progressive ban system** (escalating penalties)
- **Permanent bans** for persistent attackers
- **Automatic unban** with background cleanup threads

### Operational Excellence
- **Real-time dashboard** with auto-refresh
- **RESTful API** for external monitoring
- **Health check endpoint** for uptime monitoring
- **Systemd integration** for production deployment
- **Comprehensive logging** for debugging

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.8+ | Core application logic |
| **Web Framework** | Flask | Dashboard and API |
| **Data Structures** | collections.deque | Sliding windows |
| **Statistics** | statistics module | Baseline calculation |
| **System Monitoring** | psutil | CPU/Memory metrics |
| **Firewall** | iptables | IP blocking |
| **Web Server** | Nginx | Traffic generation & logs |
| **Frontend** | HTML/CSS/JS | Dashboard UI |

---

## 🤔 Design Decisions

### Why Python?
- **Rapid development** - Quick prototyping and iteration
- **Rich ecosystem** - Libraries for statistics, networking, system operations
- **Readable code** - Easy to understand and maintain
- **Cross-platform** - Runs on any Linux distribution

### Why deque?
- **O(1) operations** - Fast insertions and deletions at both ends
- **Memory efficient** - No need to shift elements
- **Thread-safe** - With proper locking mechanisms
- **Built-in** - No external dependencies

### Why iptables?
- **Kernel-level** - Blocks packets before they reach application
- **Zero overhead** - No performance impact on application
- **Native Linux** - Available on all Linux distributions
- **Battle-tested** - Industry standard for 20+ years

### Why Z-score?
- **Statistical rigor** - Based on probability theory
- **Adaptive** - Adjusts to traffic patterns automatically
- **Interpretable** - Clear threshold (3σ = 99.7% confidence)
- **Industry standard** - Used by major cloud providers

---

## 📚 Further Reading

- [Statistical Process Control](https://en.wikipedia.org/wiki/Statistical_process_control)
- [Z-score and Standard Deviation](https://www.statisticshowto.com/probability-and-statistics/z-score/)
- [Linux iptables Guide](https://www.digitalocean.com/community/tutorials/iptables-essentials-common-firewall-rules-and-commands)
- [Python collections.deque](https://docs.python.org/3/library/collections.html#collections.deque)
- [DDoS Attack Patterns](https://www.cloudflare.com/learning/ddos/what-is-a-ddos-attack/)

---

## 👨‍💻 Author

**Olaoluwa Afolami**
- Role: DevOps/Cloud Engineer
- HNG Stage: 3
- Year: 2026

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- HNG Internship Program for the challenge
- The Python community for excellent libraries
- Linux kernel developers for iptables
- Statistical pioneers for anomaly detection theory

---

## 🔗 Repository

**GitHub:** https://github.com/laoluafolami/hng14-stage3-http-anomally-detection

**Blog Post:** https://laoluafolami.hashnode.dev/building-a-real-time-anomaly-detection-system-a-complete-beginner-s-guide

---

