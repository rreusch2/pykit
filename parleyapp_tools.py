"""
ParleyApp ChatKit Tools
Integrations with web search, StatMuse, and sports data APIs
"""

import os
import json
import asyncio
from typing import Dict, Any, List, AsyncIterator
import httpx
from datetime import datetime, timedelta
import aiohttp
from bs4 import BeautifulSoup

class WebSearchTool:
    """Web search with streaming results"""
    
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:3000")
        
    async def search_with_updates(self, query: str) -> AsyncIterator[Dict[str, Any]]:
        """Search and stream results"""
        
        # Use your existing backend's AI search
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/ai/search",
                json={"query": query, "type": "web"}
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Stream each result
                for idx, result in enumerate(results.get("results", [])):
                    yield {
                        "type": "result",
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "source": result.get("source", "Web"),
                        "url": result.get("url", ""),
                        "index": idx
                    }
                    await asyncio.sleep(0.1)  # Simulate streaming
            else:
                yield {
                    "type": "error",
                    "message": "Search failed"
                }

class SportsDataTool:
    """Interface with sports data APIs"""
    
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:3000")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    async def get_odds(self, sport: str, market_type: str = "all") -> Dict[str, Any]:
        """Get live odds from backend"""
        
        async with httpx.AsyncClient() as client:
            # Map sport names to API keys
            sport_map = {
                "MLB": "baseball_mlb",
                "WNBA": "basketball_wnba", 
                "UFC": "mma_mixed_martial_arts",
                "NFL": "americanfootball_nfl",
                "CFB": "americanfootball_ncaaf"
            }
            
            sport_key = sport_map.get(sport, sport.lower())
            
            # Get odds from your backend
            response = await client.get(
                f"{self.base_url}/api/sports-events/odds",
                params={"sport": sport_key, "market": market_type}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Format for widget display
                formatted_games = []
                for game in data.get("events", []):
                    formatted_games.append({
                        "matchup": f"{game['away_team']} @ {game['home_team']}",
                        "time": game.get("commence_time", ""),
                        "spread": game.get("spread", "N/A"),
                        "total": game.get("total", "N/A"),
                        "home_ml": game.get("home_ml", "N/A"),
                        "away_ml": game.get("away_ml", "N/A")
                    })
                
                return {"games": formatted_games}
            
            return {"games": []}
    
    async def get_player_props(self, sport: str, prop_type: str = "all") -> Dict[str, Any]:
        """Get player props from database"""
        
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}"
            }
            
            # Query player props
            response = await client.get(
                f"{self.supabase_url}/rest/v1/player_props_odds",
                headers=headers,
                params={
                    "select": "*,players(*),sports_events(*)",
                    "sports_events.sport": f"eq.{sport}",
                    "limit": "20",
                    "order": "created_at.desc"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            
            return {"props": []}

class StatMuseTool:
    """StatMuse integration"""
    
    def __init__(self):
        self.api_url = os.getenv("STATMUSE_URL", "http://localhost:5001")
    
    async def query(self, question: str) -> Dict[str, Any]:
        """Query StatMuse"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/query",
                    json={"query": question}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        "answer": data.get("answer", ""),
                        "visual_context": data.get("visual_context", ""),
                        "data": data.get("data", {})
                    }
                    
            except Exception as e:
                print(f"StatMuse error: {e}")
                
        return {
            "answer": "Unable to fetch StatMuse data",
            "visual_context": "",
            "data": {}
        }

class BettingAnalysisTool:
    """Advanced betting analysis"""
    
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:3000")
    
    async def analyze_value(self, bet: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze betting value"""
        
        # Calculate implied probability
        odds = bet.get("odds", -110)
        if odds > 0:
            implied_prob = 100 / (odds + 100)
        else:
            implied_prob = abs(odds) / (abs(odds) + 100)
        
        # Get historical hit rate (you'd query your database)
        historical_rate = await self._get_historical_rate(bet)
        
        # Calculate edge
        edge = historical_rate - implied_prob
        
        return {
            "implied_probability": f"{implied_prob:.1f}%",
            "historical_rate": f"{historical_rate:.1f}%", 
            "edge": f"{edge:+.1f}%",
            "recommendation": "BET" if edge > 3 else "PASS",
            "confidence": self._calculate_confidence(edge)
        }
    
    async def _get_historical_rate(self, bet: Dict[str, Any]) -> float:
        """Get historical hit rate from database"""
        
        # This would query your historical data
        # For now, return a mock value
        return 55.0
    
    def _calculate_confidence(self, edge: float) -> str:
        """Calculate confidence level"""
        
        if edge >= 10:
            return "🔥 MAX"
        elif edge >= 7:
            return "⭐ HIGH"
        elif edge >= 5:
            return "✅ SOLID"
        elif edge >= 3:
            return "👍 DECENT"
        else:
            return "⚠️ LOW"
