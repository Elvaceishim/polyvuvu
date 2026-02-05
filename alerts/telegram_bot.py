"""
Telegram Alert Bot for Polyvuvu

Sends edge alerts to a configured Telegram channel.
"""
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import config


class TelegramAlertBot:
    """Telegram bot for sending prediction market alerts."""
    
    def __init__(self, token: str = None, channel_id: str = None):
        self.token = token or config.TELEGRAM_BOT_TOKEN
        self.channel_id = channel_id or config.TELEGRAM_CHANNEL_ID
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.channel_id:
            raise ValueError("TELEGRAM_CHANNEL_ID is required")
        
        self.bot = Bot(token=self.token)
    
    async def _send_message(self, text: str, parse_mode: str = ParseMode.MARKDOWN) -> bool:
        """Send a message to the configured channel."""
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=text,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False
    
    def send_alert(self, message: str) -> bool:
        """
        Send an alert message to the Telegram channel.
        
        Args:
            message: Formatted alert message
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Use a single event loop to avoid "Event loop is closed" errors
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._send_message(message))
    
    def send_edge_alert(
        self,
        market_name: str,
        confidence: int,
        reasoning: str,
        odds: dict = None,
        recommended: str = None
    ) -> bool:
        """
        Send a formatted edge alert.
        
        Args:
            market_name: Name of the market
            confidence: Confidence score (1-10)
            reasoning: 2-sentence reasoning
            odds: Dict of outcome -> probability
            recommended: Recommended position (optional)
            
        Returns:
            True if sent successfully
        """
        confidence_bar = "🟢" * (confidence // 2) + "⚪" * (5 - confidence // 2)
        
        odds_str = ""
        if odds:
            odds_str = " | ".join(f"{k}: {v}%" for k, v in odds.items())
        
        message = f"""
🎯 *EDGE ALERT*

📈 *Market:* {market_name}

📊 *Odds:* {odds_str}
💪 *Confidence:* {confidence_bar} ({confidence}/10)
"""
        
        if recommended:
            message += f"🎲 *Recommended:* {recommended}\n"
        
        message += f"\n💡 *Analysis:* {reasoning}"
        
        return self.send_alert(message.strip())
    
    def send_test_alert(self) -> bool:
        """Send a test message to verify the bot is working."""
        message = """
🤖 *Polyvuvu Test Alert*

✅ Connection successful!
Your prediction market bot is ready to send alerts.

_This is a test message._
"""
        return self.send_alert(message.strip())


# Convenience functions
_bot = None

def _get_bot() -> TelegramAlertBot:
    """Get or create singleton bot instance."""
    global _bot
    if _bot is None:
        _bot = TelegramAlertBot()
    return _bot

def send_alert(message: str) -> bool:
    """Send an alert message."""
    return _get_bot().send_alert(message)

def send_test_alert() -> bool:
    """Send a test alert to verify configuration."""
    return _get_bot().send_test_alert()


if __name__ == "__main__":
    # Quick test
    print("Testing Telegram Alert Bot...")
    
    try:
        success = send_test_alert()
        if success:
            print("✅ Test alert sent successfully!")
        else:
            print("❌ Failed to send test alert")
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID are set in .env")
