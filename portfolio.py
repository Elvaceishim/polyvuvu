"""
Polyvuvu Portfolio Manager (Paper Trading)

Tracks virtual trades based on edge alerts to calculate performance.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import TypedDict, List

from polymarket.fetcher import get_market, Market

PORTFOLIO_FILE = Path.home() / ".config/polyvuvu/portfolio.json"

class Trade(TypedDict):
    id: str  # Polymarket ID (condition_id or slug)
    question: str
    position: str  # "Yes" or "No"
    entry_price: float
    confidence: int
    entry_date: str
    status: str  # "open", "won", "lost"
    exit_price: float | None
    pnl: float | None
    resolved_date: str | None


def _load_portfolio() -> List[Trade]:
    if not PORTFOLIO_FILE.exists():
        return []
    try:
        return json.loads(PORTFOLIO_FILE.read_text())
    except Exception:
        return []


def _save_portfolio(trades: List[Trade]):
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    PORTFOLIO_FILE.write_text(json.dumps(trades, indent=2))


def add_trade(market: Market, position: str, confidence: int):
    """Record a new paper trade."""
    trades = _load_portfolio()
    
    # Check if already trading this market
    if any(t["id"] == market.id for t in trades if t["status"] == "open"):
        return
    
    # Get price for the position
    # Market prices are usually {"Yes": 0.35, "No": 0.65}
    entry_price = market.outcome_prices.get(position, 0.5)
    
    trade: Trade = {
        "id": market.id,
        "question": market.question,
        "position": position,
        "entry_price": entry_price,
        "confidence": confidence,
        "entry_date": datetime.now().isoformat(),
        "status": "open",
        "exit_price": None,
        "pnl": None,
        "resolved_date": None
    }
    
    trades.append(trade)
    _save_portfolio(trades)
    print(f"   📝 Paper trade recorded: {position} on '{market.question[:30]}...' @ {entry_price}")


def get_performance_summary() -> dict:
    """Calculate win rate and PnL."""
    trades = _load_portfolio()
    
    closed = [t for t in trades if t["status"] != "open"]
    open_trades = [t for t in trades if t["status"] == "open"]
    
    if not closed:
        return {
            "total_trades": len(trades),
            "open_trades": len(open_trades),
            "closed_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "roi": 0.0
        }
    
    wins = [t for t in closed if t["status"] == "won"]
    total_pnl = sum(t["pnl"] for t in closed if t["pnl"] is not None)
    invested = sum(1.0 for t in closed) # Assuming $1 bet per trade
    
    return {
        "total_trades": len(trades),
        "open_trades": len(open_trades),
        "closed_trades": len(closed),
        "wins": len(wins),
        "win_rate": (len(wins) / len(closed)) * 100,
        "total_pnl": total_pnl, # Total units won/lost
        "roi": (total_pnl / invested) * 100 if invested > 0 else 0
    }
