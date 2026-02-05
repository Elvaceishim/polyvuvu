"""
Polyvuvu Heartbeat Module

Handles periodic check-ins and tracking for:
- Market scanning
- Moltbook notifications
- Status updates
"""
import json
from datetime import datetime
from pathlib import Path
import requests

from config import config


HEARTBEAT_FILE = Path.home() / ".config/polyvuvu/heartbeat.json"
MOLTBOOK_API = "https://www.moltbook.com/api/v1"


def _load_heartbeat() -> dict:
    """Load heartbeat data from file."""
    if not HEARTBEAT_FILE.exists():
        return {}
    try:
        return json.loads(HEARTBEAT_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {}


def _save_heartbeat(data: dict) -> None:
    """Save heartbeat data to file."""
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.write_text(json.dumps(data, indent=2))


def update_heartbeat(task: str) -> None:
    """Record that a heartbeat task was completed."""
    data = _load_heartbeat()
    data[task] = datetime.now().isoformat()
    _save_heartbeat(data)


def time_since_last(task: str) -> float:
    """
    Get hours since last check for a task.
    
    Returns:
        Hours since last check, or infinity if never checked.
    """
    data = _load_heartbeat()
    if task not in data:
        return float('inf')
    
    try:
        last = datetime.fromisoformat(data[task])
        return (datetime.now() - last).total_seconds() / 3600
    except (ValueError, TypeError):
        return float('inf')


def check_moltbook_status(verbose: bool = False) -> dict | None:
    """
    Check agent status on Moltbook.
    
    Returns:
        Status dict or None if failed.
    """
    if not config.MOLTBOOK_API_KEY:
        return None
    
    try:
        response = requests.get(
            f"{MOLTBOOK_API}/agents/status",
            headers={"Authorization": f"Bearer {config.MOLTBOOK_API_KEY}"},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if verbose:
            status = result.get("status", "unknown")
            print(f"   🦞 Moltbook status: {status}")
        
        return result
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Moltbook status check failed: {e}")
        return None


def check_dm_activity(verbose: bool = False) -> dict | None:
    """
    Check for DM activity (requests and unread messages).
    
    Returns:
        Activity summary dict or None.
    """
    if not config.MOLTBOOK_API_KEY:
        return None
    
    try:
        response = requests.get(
            f"{MOLTBOOK_API}/agents/dm/check",
            headers={"Authorization": f"Bearer {config.MOLTBOOK_API_KEY}"},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if verbose:
            if result.get("has_activity"):
                print(f"   📬 DM Activity: {result.get('summary')}")
            else:
                print(f"   📭 No new DMs")
        
        return result
    except Exception as e:
        if verbose:
            print(f"   ⚠️ DM check failed: {e}")
        return None


def get_moltbook_feed(limit: int = 5, verbose: bool = False) -> list:
    """
    Get personalized feed from Moltbook.
    
    Returns:
        List of posts or empty list.
    """
    if not config.MOLTBOOK_API_KEY:
        return []
    
    try:
        response = requests.get(
            f"{MOLTBOOK_API}/feed",
            headers={"Authorization": f"Bearer {config.MOLTBOOK_API_KEY}"},
            params={"limit": limit},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        posts = result.get("posts", [])
        
        if verbose and posts:
            print(f"   📰 Feed: {len(posts)} recent posts in your network")
        
        return posts
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Feed fetch failed: {e}")
        return []


def run_moltbook_heartbeat(verbose: bool = False) -> None:
    """
    Run Moltbook heartbeat check.
    
    Checks status, DMs, and feed if 4+ hours since last check.
    """
    hours = time_since_last("moltbook_check")
    
    if hours < 4:
        if verbose:
            remaining = 4 - hours
            print(f"   ⏰ Moltbook check not due (next in {remaining:.1f}h)")
        return
    
    if verbose:
        print("\n🦞 Running Moltbook heartbeat...")
    
    # Check status (claim verification)
    check_moltbook_status(verbose=verbose)
    
    # Check DMs (requests & messages)
    check_dm_activity(verbose=verbose)

    # Check Feed (what are my friends doing?)
    get_moltbook_feed(verbose=verbose)
    
    # Update heartbeat tracker
    update_heartbeat("moltbook_check")
    
    if verbose:
        print("   ✅ Moltbook heartbeat complete")


def get_heartbeat_summary() -> dict:
    """Get summary of all heartbeat tasks."""
    data = _load_heartbeat()
    summary = {}
    
    for task, timestamp in data.items():
        try:
            last = datetime.fromisoformat(timestamp)
            hours_ago = (datetime.now() - last).total_seconds() / 3600
            summary[task] = {
                "last_run": timestamp,
                "hours_ago": round(hours_ago, 2)
            }
        except (ValueError, TypeError):
            summary[task] = {"last_run": timestamp, "hours_ago": None}
    
    return summary


if __name__ == "__main__":
    # Test heartbeat functionality
    print("Polyvuvu Heartbeat Status")
    print("=" * 40)
    
    summary = get_heartbeat_summary()
    if not summary:
        print("No heartbeat records yet.")
    else:
        for task, info in summary.items():
            hours = info.get("hours_ago")
            if hours is not None:
                print(f"  {task}: {hours:.1f} hours ago")
            else:
                print(f"  {task}: {info['last_run']}")
    
    print("\nRunning Moltbook heartbeat check...")
    run_moltbook_heartbeat(verbose=True)
