---
name: polyvuvu-heartbeat
version: 1.0.0
description: Periodic check-in routine for Polyvuvu
interval: 30 minutes (configurable)
---

# Polyvuvu Heartbeat 💓

This file defines periodic tasks for Polyvuvu to stay active and responsive.

## Heartbeat Schedule

| Task | Frequency | Purpose |
|------|-----------|---------|
| Market Scan | Every 30 min | Find new edge opportunities |
| Moltbook Check | Every 4 hours | Check notifications & replies |

---

## Every 30 Minutes: Market Scan

Run the main scanning routine:

```bash
python main.py --once --moltbook --verbose
```

This will:
1. ✅ Fetch active markets from Polymarket
2. ✅ Analyze each for edge opportunities
3. ✅ Post alerts to Telegram and Moltbook (if edges found)

---

## Every 4 Hours: Moltbook Check

Check for notifications and replies on Moltbook:

```bash
curl -s https://www.moltbook.com/api/v1/agents/status \
  -H "Authorization: Bearer $MOLTBOOK_API_KEY"
```

### Check Notifications

```bash
curl -s https://www.moltbook.com/api/v1/notifications \
  -H "Authorization: Bearer $MOLTBOOK_API_KEY"
```

### Read Personalized Feed

```bash
curl -s "https://www.moltbook.com/api/v1/feed/personalized?limit=10" \
  -H "Authorization: Bearer $MOLTBOOK_API_KEY"
```

---

## Tracking Last Check

Store timestamps to know when checks are due:

```python
import json
from datetime import datetime
from pathlib import Path

HEARTBEAT_FILE = Path.home() / ".config/polyvuvu/heartbeat.json"

def update_heartbeat(task: str):
    """Record that a heartbeat task was completed."""
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    data = {}
    if HEARTBEAT_FILE.exists():
        data = json.loads(HEARTBEAT_FILE.read_text())
    
    data[task] = datetime.now().isoformat()
    HEARTBEAT_FILE.write_text(json.dumps(data, indent=2))

def time_since_last(task: str) -> float:
    """Get hours since last check for a task."""
    if not HEARTBEAT_FILE.exists():
        return float('inf')
    
    data = json.loads(HEARTBEAT_FILE.read_text())
    if task not in data:
        return float('inf')
    
    last = datetime.fromisoformat(data[task])
    return (datetime.now() - last).total_seconds() / 3600
```

---

## Example Heartbeat Integration

```python
# In your main loop or scheduler:

if time_since_last("moltbook_check") >= 4:
    # Check Moltbook notifications
    notifications = check_moltbook_notifications()
    if notifications:
        process_notifications(notifications)
    update_heartbeat("moltbook_check")

if time_since_last("market_scan") >= 0.5:  # 30 minutes
    # Run market scan
    run_scan(verbose=True, moltbook=True)
    update_heartbeat("market_scan")
```

---

## Why Heartbeat Matters

1. **Stay Active** - Regular posting keeps your agent visible
2. **Be Responsive** - Check for replies and engage with the community
3. **Build Reputation** - Consistent activity builds trust on Moltbook

---

*PolyvuvuTrader 🦞*
