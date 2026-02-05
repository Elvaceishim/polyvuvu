"""
Polymarket Gamma API Client
Fetches market data from Polymarket's public read-only API.

API Documentation: https://docs.polymarket.com/
Base URL: https://gamma-api.polymarket.com
"""
import requests
from typing import Optional
from dataclasses import dataclass
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import config


@dataclass
class Market:
    """Represents a Polymarket market."""
    id: str
    question: str
    slug: str
    outcome_prices: list[float]  # Probabilities for each outcome
    outcomes: list[str]  # Outcome names (e.g., ["Yes", "No"])
    volume: float
    liquidity: float
    end_date: Optional[str] = None
    description: Optional[str] = None
    
    @property
    def implied_probability(self) -> dict[str, float]:
        """Get implied probability for each outcome as a percentage."""
        return {
            outcome: round(price * 100, 1)
            for outcome, price in zip(self.outcomes, self.outcome_prices)
        }
    
    def __str__(self) -> str:
        probs = ", ".join(f"{k}: {v}%" for k, v in self.implied_probability.items())
        return f"{self.question} ({probs})"


class PolymarketFetcher:
    """Client for Polymarket's Gamma API."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.POLYMARKET_GAMMA_API
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Polyvuvu/1.0"
        })
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_active_markets(self, limit: int = 50) -> list[Market]:
        """
        Fetch active (non-closed) markets from Polymarket.
        
        Args:
            limit: Maximum number of markets to fetch
            
        Returns:
            List of Market objects with current odds
        """
        params = {
            "closed": "false",
            "limit": limit,
            "order": "volume",  # Sort by trading volume
            "ascending": "false"  # Highest volume first
        }
        
        data = self._get("/markets", params=params)
        markets = []
        
        for item in data:
            try:
                # Parse outcome prices from string format
                outcome_prices_str = item.get("outcomePrices", "[]")
                if isinstance(outcome_prices_str, str):
                    # Handle JSON string format: "[\"0.5\", \"0.5\"]"
                    import json
                    outcome_prices = [float(p) for p in json.loads(outcome_prices_str)]
                else:
                    outcome_prices = [float(p) for p in outcome_prices_str]
                
                # Parse outcomes
                outcomes_str = item.get("outcomes", "[]")
                if isinstance(outcomes_str, str):
                    import json
                    outcomes = json.loads(outcomes_str)
                else:
                    outcomes = outcomes_str
                
                market = Market(
                    id=item.get("id", ""),
                    question=item.get("question", "Unknown"),
                    slug=item.get("slug", ""),
                    outcome_prices=outcome_prices,
                    outcomes=outcomes,
                    volume=float(item.get("volume", 0)),
                    liquidity=float(item.get("liquidity", 0)),
                    end_date=item.get("endDate"),
                    description=item.get("description")
                )
                markets.append(market)
            except (ValueError, KeyError, TypeError) as e:
                # Skip malformed market data
                continue
        
        return markets
    
    def get_market_details(self, slug: str) -> Optional[Market]:
        """
        Get detailed information for a specific market by slug.
        
        Args:
            slug: Market's unique slug identifier
            
        Returns:
            Market object or None if not found
        """
        try:
            data = self._get(f"/markets/slug/{slug}")
            
            outcome_prices_str = data.get("outcomePrices", "[]")
            if isinstance(outcome_prices_str, str):
                import json
                outcome_prices = [float(p) for p in json.loads(outcome_prices_str)]
            else:
                outcome_prices = [float(p) for p in outcome_prices_str]
            
            outcomes_str = data.get("outcomes", "[]")
            if isinstance(outcomes_str, str):
                import json
                outcomes = json.loads(outcomes_str)
            else:
                outcomes = outcomes_str
            
            return Market(
                id=data.get("id", ""),
                question=data.get("question", "Unknown"),
                slug=data.get("slug", ""),
                outcome_prices=outcome_prices,
                outcomes=outcomes,
                volume=float(data.get("volume", 0)),
                liquidity=float(data.get("liquidity", 0)),
                end_date=data.get("endDate"),
                description=data.get("description")
            )
        except requests.RequestException:
            return None
    
    def get_market(self, id: str) -> Optional[Market]:
        """
        Get market details by ID.
        
        Args:
            id: Market ID (condition ID or internal ID)
            
        Returns:
            Market object or None
        """
        try:
            data = self._get(f"/markets/{id}")
            # Reuse parsing logic - ideally should be a separate method but duplication is safe here
            outcome_prices_str = data.get("outcomePrices", "[]")
            if isinstance(outcome_prices_str, str):
                import json
                outcome_prices = [float(p) for p in json.loads(outcome_prices_str)]
            else:
                outcome_prices = [float(p) for p in outcome_prices_str]
            
            outcomes_str = data.get("outcomes", "[]")
            if isinstance(outcomes_str, str):
                import json
                outcomes = json.loads(outcomes_str)
            else:
                outcomes = outcomes_str
            
            return Market(
                id=data.get("id", ""),
                question=data.get("question", "Unknown"),
                slug=data.get("slug", ""),
                outcome_prices=outcome_prices,
                outcomes=outcomes,
                volume=float(data.get("volume", 0)),
                liquidity=float(data.get("liquidity", 0)),
                end_date=data.get("endDate"),
                description=data.get("description")
            )
        except requests.RequestException:
            return None
    
    def get_tags(self) -> list[dict]:
        """Get available market categories/tags."""
        return self._get("/tags")
    
    def get_markets_by_tag(self, tag_id: str, limit: int = 20) -> list[Market]:
        """
        Get markets filtered by a specific tag/category.
        
        Args:
            tag_id: Tag ID to filter by
            limit: Maximum number of markets
            
        Returns:
            List of Market objects
        """
        params = {
            "closed": "false",
            "tag_id": tag_id,
            "limit": limit
        }
        data = self._get("/markets", params=params)
        
        markets = []
        for item in data:
            try:
                outcome_prices_str = item.get("outcomePrices", "[]")
                if isinstance(outcome_prices_str, str):
                    import json
                    outcome_prices = [float(p) for p in json.loads(outcome_prices_str)]
                else:
                    outcome_prices = [float(p) for p in outcome_prices_str]
                
                outcomes_str = item.get("outcomes", "[]")
                if isinstance(outcomes_str, str):
                    import json
                    outcomes = json.loads(outcomes_str)
                else:
                    outcomes = outcomes_str
                
                market = Market(
                    id=item.get("id", ""),
                    question=item.get("question", "Unknown"),
                    slug=item.get("slug", ""),
                    outcome_prices=outcome_prices,
                    outcomes=outcomes,
                    volume=float(item.get("volume", 0)),
                    liquidity=float(item.get("liquidity", 0)),
                    end_date=item.get("endDate"),
                    description=item.get("description")
                )
                markets.append(market)
            except (ValueError, KeyError, TypeError):
                continue
        
        return markets


# Convenience functions for simple usage
_fetcher = None

def _get_fetcher() -> PolymarketFetcher:
    """Get or create singleton fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = PolymarketFetcher()
    return _fetcher

def get_active_markets(limit: int = 50) -> list[Market]:
    """Fetch active markets from Polymarket."""
    return _get_fetcher().get_active_markets(limit)

def get_market_details(slug: str) -> Optional[Market]:
    """Get details for a specific market."""
    return _get_fetcher().get_market_details(slug)

def get_market(id: str) -> Optional[Market]:
    """Get market by ID."""
    return _get_fetcher().get_market(id)


if __name__ == "__main__":
    # Quick test
    print("Fetching active markets from Polymarket...")
    markets = get_active_markets(limit=5)
    print(f"\nFound {len(markets)} markets:\n")
    for market in markets:
        print(f"  • {market}")
        print(f"    Volume: ${market.volume:,.0f} | Liquidity: ${market.liquidity:,.0f}")
        print()
