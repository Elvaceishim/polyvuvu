"""
Polyvuvu - AI-Powered Prediction Market Alert Bot

Main entry point that orchestrates:
1. Fetching markets from Polymarket
2. Analyzing them with AI (OpenRouter/Gemini)
3. Sending edge alerts via Telegram and/or Moltbook
"""
import argparse
import schedule
import time
from datetime import datetime

from config import config
from polymarket.fetcher import get_active_markets, Market
from analysis.gemini_analyzer import analyze_market, EdgeAnalysis
from alerts.telegram_bot import send_alert, send_test_alert
from heartbeat import run_moltbook_heartbeat, update_heartbeat, get_heartbeat_summary
from portfolio import add_trade, get_performance_summary


def analyze_and_alert(
    markets: list[Market], 
    verbose: bool = False,
    post_to_moltbook: bool = False,
    ask_peer: str = None
) -> int:
    """
    Analyze markets and send alerts for detected edges.
    
    Args:
        markets: List of markets to analyze
        verbose: Print detailed progress
        post_to_moltbook: Also post to Moltbook AI social network
        ask_peer: Name of agent to ask for review (sends DM)
        
    Returns:
        Number of alerts sent
    """
    # Lazy import to avoid errors if not using Moltbook
    moltbook_post = None
    moltbook_dm = None
    
    if post_to_moltbook or ask_peer:
        try:
            from moltbook.client import post_edge_alert, send_dm
            moltbook_post = post_edge_alert
            moltbook_dm = send_dm
            if verbose and post_to_moltbook:
                print("   📡 Moltbook posting enabled")
            if verbose and ask_peer:
                print(f"   🤝 Peer review: enabled (asking {ask_peer})")
        except Exception as e:
            print(f"   ⚠️ Moltbook not available: {e}")
    
    alerts_sent = 0
    
    for i, market in enumerate(markets):
        if verbose:
            print(f"  [{i+1}/{len(markets)}] Analyzing: {market.question[:50]}...")
        
        try:
            analysis = analyze_market(
                question=market.question,
                outcomes=market.outcomes,
                outcome_prices=market.outcome_prices,
                description=market.description
            )
            
            # Only alert if edge detected with sufficient confidence
            if analysis.has_edge and analysis.confidence_score >= config.MIN_CONFIDENCE_THRESHOLD:
                if verbose:
                    print(f"    🎯 Edge detected! Confidence: {analysis.confidence_score}/10")
                
                # Record paper trade
                add_trade(market, analysis.recommended_position, analysis.confidence_score)
                
                # Peer Review (DM)
                if ask_peer and moltbook_dm:
                    msg = (
                        f"Hey {ask_peer}! I found an edge on: '{market.question}'.\n"
                        f"My confidence: {analysis.confidence_score}/10.\n"
                        f"Reasoning: {analysis.reasoning[:200]}...\n"
                        f"What do you think?"
                    )
                    if moltbook_dm(ask_peer, msg):
                        if verbose:
                            print(f"    📨 Sent review request to {ask_peer}")
                
                # Send to Telegram
                message = analysis.to_alert_message()
                if send_alert(message):
                    alerts_sent += 1
                    if verbose:
                        print(f"    ✅ Telegram alert sent!")
                
                # Post to Moltbook if enabled
                if moltbook_post:
                    if moltbook_post(
                        market_question=analysis.market_question,
                        confidence=analysis.confidence_score,
                        reasoning=analysis.reasoning,
                        odds=analysis.current_odds,
                        recommended=analysis.recommended_position
                    ):
                        if verbose:
                            print(f"    ✅ Posted to Moltbook!")
                    
            elif verbose and analysis.confidence_score >= 5:
                print(f"    ⚪ Potential edge (confidence: {analysis.confidence_score}/10)")
                
        except Exception as e:
            if verbose:
                print(f"    ❌ Error: {e}")
            continue
        
        # Rate limiting: wait between API calls to stay within free tier
        if i < len(markets) - 1:
            time.sleep(6)
    
    return alerts_sent


def run_scan(verbose: bool = False, moltbook: bool = False, ask_peer: str = None) -> None:
    """Run a single market scan."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"🔍 Polyvuvu Scan - {timestamp}")
    print(f"{'='*50}")
    
    # Check configuration
    missing = config.validate()
    if missing:
        print(f"❌ Missing configuration: {', '.join(missing)}")
        print("Please set up your .env file with the required keys.")
        return
    
    # Fetch markets
    print("\n📊 Fetching active markets from Polymarket...")
    try:
        markets = get_active_markets(limit=10)
        print(f"   Found {len(markets)} active markets")
    except Exception as e:
        print(f"❌ Failed to fetch markets: {e}")
        return
    
    if not markets:
        print("   No markets found. Check your internet connection.")
        return
    
    # Analyze markets
    print("\n🧠 Analyzing markets with AI...")
    alerts_sent = analyze_and_alert(markets, verbose=verbose, post_to_moltbook=moltbook, ask_peer=ask_peer)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"📈 Scan complete: {alerts_sent} edge alert(s) sent")
    print(f"{'='*50}\n")


def run_scheduler(interval_minutes: int = None, moltbook: bool = False, ask_peer: str = None) -> None:
    """Run the bot on a schedule."""
    interval = interval_minutes or config.SCAN_INTERVAL_MINUTES
    
    print(f"🤖 Polyvuvu Starting...")
    print(f"   Scan interval: {interval} minutes")
    print(f"   Min confidence threshold: {config.MIN_CONFIDENCE_THRESHOLD}/10")
    if moltbook:
        print(f"   📡 Moltbook posting: enabled")
    if ask_peer:
        print(f"   🤝 Peer review: enabled (asking {ask_peer})")
    print(f"\nPress Ctrl+C to stop.\n")
    
    # Run immediately on start
    run_scan(verbose=True, moltbook=moltbook, ask_peer=ask_peer)
    
    # Schedule periodic runs
    schedule.every(interval).minutes.do(lambda: run_scan(verbose=True, moltbook=moltbook, ask_peer=ask_peer))
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n👋 Polyvuvu stopped. Goodbye!")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Polyvuvu - AI-Powered Prediction Market Alert Bot"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single scan and exit"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send a test alert to verify Telegram configuration"
    )
    parser.add_argument(
        "--moltbook",
        action="store_true",
        help="Also post edge alerts to Moltbook AI social network"
    )
    parser.add_argument(
        "--interval",
        type=int,
        help=f"Scan interval in minutes (default: {config.SCAN_INTERVAL_MINUTES})"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed progress"
    )
    parser.add_argument(
        "--heartbeat",
        action="store_true",
        help="Run heartbeat check (Moltbook status & notifications)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show heartbeat status summary"
    )
    parser.add_argument(
        "--portfolio",
        action="store_true",
        help="Show paper trading performance portfolio"
    )
    parser.add_argument(
        "--ask-peer",
        type=str,
        help="Agent name to ask for peer review on high confidence alerts"
    )
    
    args = parser.parse_args()
    
    if args.portfolio:
        print("💼 Paper Trading Portfolio")
        print("=" * 40)
        stats = get_performance_summary()
        print(f"  Total Trades: {stats['total_trades']}")
        print(f"  Open:         {stats['open_trades']}")
        print(f"  Closed:       {stats['closed_trades']}")
        print(f"  Win Rate:     {stats['win_rate']:.1f}%")
        print(f"  Total PnL:    {stats['total_pnl']:.2f} units")
        print(f"  ROI:          {stats['roi']:.1f}%")
        print("=" * 40)
        return

    if args.status:
        print("📊 Polyvuvu Heartbeat Status")
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
        return
    
    if args.heartbeat:
        print("💓 Running Moltbook heartbeat...")
        run_moltbook_heartbeat(verbose=True)
        return
    
    if args.test:
        print("🧪 Sending test alert to Telegram...")
        missing = config.validate()
        if "TELEGRAM_BOT_TOKEN" in missing or "TELEGRAM_CHANNEL_ID" in missing:
            print("❌ Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID in .env")
            return
        
        if send_test_alert():
            print("✅ Test alert sent successfully!")
        else:
            print("❌ Failed to send test alert. Check your configuration.")
        return
    
    if args.once:
        run_scan(verbose=args.verbose or True, moltbook=args.moltbook, ask_peer=args.ask_peer)
        update_heartbeat("market_scan")
    else:
        run_scheduler(interval_minutes=args.interval, moltbook=args.moltbook, ask_peer=args.ask_peer)


if __name__ == "__main__":
    main()

