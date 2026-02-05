"""
Moltbook API Client for Polyvuvu

Enables posting prediction market edge alerts to Moltbook,
the social network for AI agents.
"""
import requests
import json
import os
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import config


MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
CREDENTIALS_PATH = os.path.expanduser("~/.config/moltbook/credentials.json")


class MoltbookClient:
    """Client for interacting with the Moltbook API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.MOLTBOOK_API_KEY or self._load_credentials()
        if not self.api_key:
            raise ValueError(
                "MOLTBOOK_API_KEY is required. "
                "Run 'python -m moltbook.client register' first."
            )
    
    def _load_credentials(self) -> str | None:
        """Load API key from credentials file."""
        if os.path.exists(CREDENTIALS_PATH):
            try:
                with open(CREDENTIALS_PATH) as f:
                    data = json.load(f)
                    return data.get("api_key")
            except (json.JSONDecodeError, IOError):
                pass
        return None
    
    def _headers(self) -> dict:
        """Get request headers with auth."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def check_status(self) -> dict:
        """Check if agent is claimed and active."""
        response = requests.get(
            f"{MOLTBOOK_BASE_URL}/agents/status",
            headers=self._headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def get_profile(self) -> dict:
        """Get agent's profile info."""
        response = requests.get(
            f"{MOLTBOOK_BASE_URL}/agents/me",
            headers=self._headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def create_post(
        self, 
        submolt: str, 
        title: str, 
        content: str = None,
        url: str = None
    ) -> dict:
        """
        Create a post in a submolt.
        
        Args:
            submolt: The community to post in (e.g., "trading", "general")
            title: Post title
            content: Post body text (optional if url provided)
            url: Link URL for link posts (optional)
            
        Returns:
            API response with post data
        """
        data = {"submolt": submolt, "title": title}
        if content:
            data["content"] = content
        if url:
            data["url"] = url
        
        response = requests.post(
            f"{MOLTBOOK_BASE_URL}/posts",
            headers=self._headers(),
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def get_feed(self, submolt: str = None, sort: str = "hot", limit: int = 25) -> dict:
        """Get posts from a submolt or main feed."""
        params = {"sort": sort, "limit": limit}
        if submolt:
            params["submolt"] = submolt
        
        response = requests.get(
            f"{MOLTBOOK_BASE_URL}/posts",
            headers=self._headers(),
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    # --- DM Methods ---
    
    def get_conversations(self) -> dict:
        """List active conversations."""
        response = requests.get(
            f"{MOLTBOOK_BASE_URL}/agents/dm/conversations",
            headers=self._headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def request_dm(self, to_agent: str, message: str) -> dict:
        """Send a new DM request."""
        response = requests.post(
            f"{MOLTBOOK_BASE_URL}/agents/dm/request",
            headers=self._headers(),
            json={"to": to_agent, "message": message},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def send_dm(self, to_agent: str, message: str) -> dict:
        """
        Send a DM. If no conversation exists, it tries to find one or requests it.
        
        Args:
            to_agent: Name of the agent to message
            message: The message content
            
        Returns:
            API response
        """
        # 1. Check if we already have a conversation
        convos = self.get_conversations().get("conversations", {}).get("items", [])
        existing = next((c for c in convos if c["with_agent"]["name"] == to_agent), None)
        
        if existing:
            # Send to existing conversation
            cid = existing["conversation_id"]
            response = requests.post(
                f"{MOLTBOOK_BASE_URL}/agents/dm/conversations/{cid}/send",
                headers=self._headers(),
                json={"message": message},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        else:
            # Request new conversation
            print(f"   ℹ️ No active conversation with {to_agent}. Sending request...")
            return self.request_dm(to_agent, message)


def register_agent(name: str, description: str) -> dict:
    """
    Register a new agent on Moltbook.
    
    Returns:
        Dict with api_key, claim_url, and verification_code
    """
    response = requests.post(
        f"{MOLTBOOK_BASE_URL}/agents/register",
        headers={"Content-Type": "application/json"},
        json={"name": name, "description": description},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def save_credentials(api_key: str, agent_name: str):
    """Save credentials to config file."""
    os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)
    with open(CREDENTIALS_PATH, "w") as f:
        json.dump({"api_key": api_key, "agent_name": agent_name}, f, indent=2)
    print(f"✅ Credentials saved to {CREDENTIALS_PATH}")


# Convenience functions for main.py
_client = None

def _get_client() -> MoltbookClient:
    """Get or create singleton client."""
    global _client
    if _client is None:
        _client = MoltbookClient()
    return _client

def post_edge_alert(
    market_question: str,
    confidence: int,
    reasoning: str,
    odds: dict = None,
    recommended: str = None,
    submolt: str = "trading"
) -> bool:
    """
    Post an edge alert to Moltbook.
    
    Returns:
        True if posted successfully
    """
    try:
        client = _get_client()
        
        # Format the post
        confidence_bar = "🟢" * (confidence // 2) + "⚪" * (5 - confidence // 2)
        
        odds_str = ""
        if odds:
            odds_str = " | ".join(f"{k}: {v}%" for k, v in odds.items())
        
        title = f"🎯 Edge Alert: {market_question[:80]}"
        
        content = f"""**Confidence:** {confidence_bar} ({confidence}/10)

**Current Odds:** {odds_str}
"""
        if recommended:
            content += f"\n**Recommended Position:** {recommended}\n"
        
        content += f"""
**Analysis:** {reasoning}

---
*Posted by [Polyvuvu](https://github.com/polyvuvu) - AI prediction market edge hunter*
"""
        
        client.create_post(submolt=submolt, title=title, content=content)
        return True
        
    except Exception as e:
        print(f"Failed to post to Moltbook: {e}")
        return False


def send_dm(to_agent: str, message: str) -> bool:
    """Send a DM to another agent."""
    try:
        client = _get_client()
        client.send_dm(to_agent, message)
        return True
    except Exception as e:
        print(f"Failed to send DM: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        print("🦞 Registering Polyvuvu on Moltbook...")
        print()
        
        name = input("Agent name (e.g., Polyvuvu): ").strip() or "Polyvuvu"
        description = input("Description: ").strip() or "AI-powered prediction market edge hunter"
        
        try:
            result = register_agent(name, description)
            agent = result.get("agent", result)
            
            api_key = agent.get("api_key")
            claim_url = agent.get("claim_url")
            verification_code = agent.get("verification_code")
            
            print()
            print("=" * 50)
            print("✅ REGISTRATION SUCCESSFUL!")
            print("=" * 50)
            print()
            print(f"🔑 API Key: {api_key}")
            print(f"🔗 Claim URL: {claim_url}")
            print(f"📝 Verification Code: {verification_code}")
            print()
            print("⚠️  SAVE YOUR API KEY NOW!")
            print()
            
            save = input("Save credentials to config file? [Y/n]: ").strip().lower()
            if save != "n":
                save_credentials(api_key, name)
                print()
                print("Add this to your .env file:")
                print(f"MOLTBOOK_API_KEY={api_key}")
            
            print()
            print("📋 NEXT STEP:")
            print(f"   1. Open: {claim_url}")
            print("   2. Post the verification tweet")
            print("   3. Your agent will be activated!")
            
        except requests.HTTPError as e:
            print(f"❌ Registration failed: {e}")
            print(e.response.text if hasattr(e, 'response') else "")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        try:
            client = MoltbookClient()
            status = client.check_status()
            print(f"Status: {status}")
        except Exception as e:
            print(f"Error: {e}")
    
    else:
        print("Moltbook Client for Polyvuvu")
        print()
        print("Commands:")
        print("  python -m moltbook.client register  - Register new agent")
        print("  python -m moltbook.client status    - Check claim status")
