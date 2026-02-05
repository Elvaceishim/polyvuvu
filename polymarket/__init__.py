"""Polymarket API client module."""
from .fetcher import PolymarketFetcher, get_active_markets, get_market_details

__all__ = ["PolymarketFetcher", "get_active_markets", "get_market_details"]
