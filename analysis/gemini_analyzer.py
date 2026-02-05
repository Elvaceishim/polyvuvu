"""
LLM Analyzer for Prediction Market Edge Detection

Supports multiple providers:
- OpenRouter (recommended - access to many models)
- Google Gemini (direct)

Set OPENROUTER_API_KEY in .env to use OpenRouter.
Set GEMINI_API_KEY in .env to use Gemini directly.
OpenRouter takes priority if both are set.
"""
import requests
from dataclasses import dataclass
from typing import Optional
import json
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import config


@dataclass
class EdgeAnalysis:
    """Result of AI edge analysis for a market."""
    market_question: str
    confidence_score: int  # 1-10
    has_edge: bool
    reasoning: str
    recommended_position: Optional[str] = None  # e.g., "Yes" or "No"
    current_odds: dict = None
    
    def to_alert_message(self) -> str:
        """Format analysis as a Telegram alert message."""
        edge_emoji = "🎯" if self.has_edge else "⚪"
        confidence_bar = "🟢" * (self.confidence_score // 2) + "⚪" * (5 - self.confidence_score // 2)
        
        odds_str = ""
        if self.current_odds:
            odds_str = " | ".join(f"{k}: {v}%" for k, v in self.current_odds.items())
        
        message = f"""
{edge_emoji} **{self.market_question}**

📊 **Current Odds:** {odds_str}
💪 **Confidence:** {confidence_bar} ({self.confidence_score}/10)
{"🎲 **Recommended:** " + self.recommended_position if self.recommended_position else ""}

💡 **Analysis:** {self.reasoning}
"""
        return message.strip()


SYSTEM_PROMPT = """You are an expert prediction market analyst specializing in edge detection.

Your job is to analyze a prediction market and determine if the current odds represent a potential "edge" - a mispricing where the true probability differs significantly from the market price.

For each market, you will:
1. Assess the current market probabilities
2. Consider any external context provided (news, statistics, trends)
3. Determine if the market is fairly priced or if there's an edge

IMPORTANT RULES:
- Be conservative. Only flag high-confidence edges (7+/10 confidence).
- Always explain your reasoning in 2-3 sentences.
- If you recommend a position, explain WHY that side is undervalued.
- Consider that markets are often efficient - edges are rare.
- Never hallucinate facts. If you don't know, say so.

Respond ONLY with valid JSON in this format:
{
    "confidence_score": <1-10>,
    "has_edge": <true/false>,
    "reasoning": "<2-3 sentence explanation>",
    "recommended_position": "<null or outcome name if edge exists>"
}
"""


class OpenRouterAnalyzer:
    """Analyzer using OpenRouter API (OpenAI-compatible)."""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or config.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        
        # Default to a fast, cheap model
        self.model = model or "google/gemini-2.0-flash-001"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def analyze_market(
        self,
        question: str,
        outcomes: list[str],
        outcome_prices: list[float],
        description: str = None,
        external_context: str = None
    ) -> EdgeAnalysis:
        """Analyze a market for potential edges."""
        
        # Build the user prompt
        odds_info = "\n".join(
            f"  - {outcome}: {price*100:.1f}%"
            for outcome, price in zip(outcomes, outcome_prices)
        )
        
        prompt = f"""Analyze this prediction market:

**Market Question:** {question}

**Current Odds:**
{odds_info}
"""
        
        if description:
            prompt += f"\n**Market Description:** {description}\n"
        
        if external_context:
            prompt += f"\n**External Context (News/Stats):** {external_context}\n"
        else:
            prompt += "\n**External Context:** None provided. Analyze based on market structure only.\n"
        
        prompt += "\nProvide your edge analysis as JSON:"
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/baysewatch",
                    "X-Title": "Polyvuvu"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30
            )
            response.raise_for_status()
            
            result_text = response.json()["choices"][0]["message"]["content"].strip()
            
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text)
            
            current_odds = {
                outcome: round(price * 100, 1)
                for outcome, price in zip(outcomes, outcome_prices)
            }
            
            return EdgeAnalysis(
                market_question=question,
                confidence_score=min(10, max(1, int(result.get("confidence_score", 5)))),
                has_edge=bool(result.get("has_edge", False)),
                reasoning=str(result.get("reasoning", "Analysis failed")),
                recommended_position=result.get("recommended_position"),
                current_odds=current_odds
            )
            
        except (json.JSONDecodeError, KeyError, TypeError, requests.RequestException) as e:
            return EdgeAnalysis(
                market_question=question,
                confidence_score=1,
                has_edge=False,
                reasoning=f"Analysis failed: {str(e)}",
                current_odds={
                    outcome: round(price * 100, 1)
                    for outcome, price in zip(outcomes, outcome_prices)
                }
            )


class GeminiAnalyzer:
    """Analyzer using Google Gemini directly."""
    
    def __init__(self, api_key: str = None):
        import google.generativeai as genai
        
        self.api_key = api_key or config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            system_instruction=SYSTEM_PROMPT
        )
    
    def analyze_market(
        self,
        question: str,
        outcomes: list[str],
        outcome_prices: list[float],
        description: str = None,
        external_context: str = None
    ) -> EdgeAnalysis:
        """Analyze a market for potential edges."""
        
        odds_info = "\n".join(
            f"  - {outcome}: {price*100:.1f}%"
            for outcome, price in zip(outcomes, outcome_prices)
        )
        
        prompt = f"""Analyze this prediction market:

**Market Question:** {question}

**Current Odds:**
{odds_info}
"""
        
        if description:
            prompt += f"\n**Market Description:** {description}\n"
        
        if external_context:
            prompt += f"\n**External Context (News/Stats):** {external_context}\n"
        else:
            prompt += "\n**External Context:** None provided. Analyze based on market structure only.\n"
        
        prompt += "\nProvide your edge analysis as JSON:"
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text)
            
            current_odds = {
                outcome: round(price * 100, 1)
                for outcome, price in zip(outcomes, outcome_prices)
            }
            
            return EdgeAnalysis(
                market_question=question,
                confidence_score=min(10, max(1, int(result.get("confidence_score", 5)))),
                has_edge=bool(result.get("has_edge", False)),
                reasoning=str(result.get("reasoning", "Analysis failed")),
                recommended_position=result.get("recommended_position"),
                current_odds=current_odds
            )
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return EdgeAnalysis(
                market_question=question,
                confidence_score=1,
                has_edge=False,
                reasoning=f"Analysis failed: {str(e)}",
                current_odds={
                    outcome: round(price * 100, 1)
                    for outcome, price in zip(outcomes, outcome_prices)
                }
            )


# Auto-select analyzer based on available API keys
_analyzer = None

def _get_analyzer():
    """Get or create analyzer instance. Prefers OpenRouter if available."""
    global _analyzer
    if _analyzer is None:
        if config.OPENROUTER_API_KEY:
            print("   Using OpenRouter API")
            _analyzer = OpenRouterAnalyzer()
        elif config.GEMINI_API_KEY:
            print("   Using Gemini API directly")
            _analyzer = GeminiAnalyzer()
        else:
            raise ValueError("Either OPENROUTER_API_KEY or GEMINI_API_KEY is required")
    return _analyzer

def analyze_market(
    question: str,
    outcomes: list[str],
    outcome_prices: list[float],
    description: str = None,
    external_context: str = None
) -> EdgeAnalysis:
    """Analyze a market for edges."""
    return _get_analyzer().analyze_market(
        question, outcomes, outcome_prices, description, external_context
    )


if __name__ == "__main__":
    print("Testing Analyzer...")
    
    try:
        analysis = analyze_market(
            question="Will Bitcoin reach $100,000 by end of 2024?",
            outcomes=["Yes", "No"],
            outcome_prices=[0.35, 0.65],
            external_context="Bitcoin is currently trading at $67,000. ETF inflows have been strong."
        )
        print(analysis.to_alert_message())
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure OPENROUTER_API_KEY or GEMINI_API_KEY is set in .env")
