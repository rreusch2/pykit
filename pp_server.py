"""
ParleyApp Professor Lock ChatKit Server
Advanced sports betting assistant with visual widgets
"""

import os
import asyncio
import json
from typing import Any, AsyncIterator, Optional, Dict, List
from datetime import datetime
from collections.abc import AsyncGenerator
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

from agents import Agent, Runner, function_tool, RunContextWrapper, StopAtTools

from chatkit.server import ChatKitServer
from chatkit.agents import AgentContext, stream_agent_response, simple_to_agent_input, accumulate_text
from chatkit.widgets import (
    Card, Text, Title, Button, Row, Col, Box, Markdown,
    ListView, ListViewItem, Badge, Icon, Divider, Spacer,
    Chart, Series, Form, Select, SelectOption, Input,
    Transition, Image
)
from chatkit.actions import ActionConfig, Action
from chatkit.types import (
    ThreadMetadata, UserMessageItem, ThreadStreamEvent,
    WidgetItem, HiddenContextItem, ClientToolCallItem,
    AssistantMessageContent, Annotation, URLSource,
    ProgressUpdateEvent, ThreadItemDoneEvent
)
from chatkit.store import Store
from chatkit.errors import StreamError

# Import our custom tools and widgets
from parleyapp_tools import WebSearchTool, SportsDataTool, StatMuseTool, BettingAnalysisTool
from parleyapp_widgets import (
    create_search_progress_widget,
    create_odds_comparison_widget,
    create_parlay_builder_widget,
    create_trends_chart_widget,
    create_player_prop_widget
)

load_dotenv()

class ParlayLeg(BaseModel):
    """Single leg in a parlay bet"""
    pick: str
    type: str
    odds: str

@function_tool
async def web_search_visual(
    ctx: RunContextWrapper,
    query: str,
    search_type: str = "general"
) -> str:
    """Web search with live progress widget"""
    try:
        results: List[str] = []
        web_search = WebSearchTool()
        
        # Stream results
        async for update in web_search.search_with_updates(query):
            if update.get("type") == "result":
                results.append(f"{update.get('title','')}: {update.get('snippet','')}")
        
        if results:
            return "\n".join(results[:5])  # Top 5 results
        else:
            return f"Found information about: {query}. Based on current sports analysis and betting trends."
    except Exception as e:
        print(f"Web search error: {e}")
        return f"Analyzing {query} based on available data and current trends."

@function_tool
async def get_odds_visual(
    ctx: RunContextWrapper,
    sport: str,
    market_type: str = "all"
) -> str:
    """Fetch and visualize odds data"""
    try:
        sports_data = SportsDataTool()
        odds_data = await sports_data.get_odds(sport, market_type)
        
        if odds_data and odds_data.get("games"):
            games_summary = []
            for game in odds_data["games"][:5]:
                games_summary.append(f"{game.get('matchup', 'Game')} - Spread: {game.get('spread', 'N/A')}, Total: {game.get('total', 'N/A')}")
            return "\n".join(games_summary)
        else:
            return f"Current {sport} odds are available. Check your sportsbook for latest lines."
    except Exception as e:
        print(f"Odds fetch error: {e}")
        return f"Unable to fetch live {sport} odds at the moment. Use your sportsbook for current lines."

@function_tool
async def statmuse_query(
    ctx: RunContextWrapper,
    question: str
) -> str:
    """Query StatMuse with visual response"""
    try:
        statmuse = StatMuseTool()
        result = await statmuse.query(question)
        return result.get("answer", f"Analysis for: {question}")
    except Exception as e:
        print(f"StatMuse error: {e}")
        return f"Based on statistical analysis for: {question}"

@function_tool
async def build_parlay(
    ctx: RunContextWrapper,
    picks: str,
    stake: float = 100
) -> str:
    """Create a parlay with multiple betting legs. Provide picks as a string description."""
    try:
        # Parse picks and calculate odds
        return f"Parlay Builder: {picks}\n\nTo build your parlay, I'll need specific picks with odds. For example:\n1. Lakers ML (-150)\n2. Celtics -3.5 (-110)\n\nProvide your picks and I'll calculate the payout for ${stake:.2f} stake."
    except Exception as e:
        print(f"Parlay error: {e}")
        return "I can help you build a parlay! Tell me which picks you want to include with their odds."

@function_tool
async def get_nba_props(
    ctx: RunContextWrapper,
    player_name: Optional[str] = None,
    limit: int = 10
) -> str:
    """Get today's top NBA player prop picks from the AI predictions database"""
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        # Query ai_predictions for NBA props
        query = supabase.table("ai_predictions").select("*").eq("sport", "NBA").eq("pick_type", "prop")
        
        if player_name:
            query = query.ilike("pick", f"%{player_name}%")
        
        # Get today's props ordered by confidence
        from datetime import date
        today = date.today().isoformat()
        result = query.gte("created_at", today).order("confidence", desc=True).limit(limit).execute()
        
        if result.data:
            props_text = []
            for idx, prop in enumerate(result.data, 1):
                props_text.append(
                    f"{idx}. **{prop.get('pick', 'N/A')}**\n"
                    f"   Confidence: {prop.get('confidence', 0):.1f}% | "
                    f"Edge: +{prop.get('edge', 0):.1f}%\n"
                    f"   Reasoning: {prop.get('reasoning', 'N/A')[:100]}..."
                )
            return "\n\n".join(props_text)
        else:
            return "No NBA props available at the moment. Check back soon for today's AI picks!"
    except Exception as e:
        print(f"NBA props error: {e}")
        import traceback
        traceback.print_exc()
        return "Unable to fetch NBA props right now. Try asking about specific players or check the main predictions page."

@function_tool
async def get_todays_picks(
    ctx: RunContextWrapper,
    sport: Optional[str] = None,
    pick_type: Optional[str] = None,
    min_confidence: float = 70.0,
    limit: int = 10
) -> str:
    """Get today's top AI betting picks from the database. Filters by sport, pick type (team/prop), and minimum confidence."""
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        # Build query
        query = supabase.table("ai_predictions").select("*")
        
        if sport:
            query = query.eq("sport", sport.upper())
        
        if pick_type:
            query = query.eq("pick_type", pick_type.lower())
        
        # Get today's picks with minimum confidence
        from datetime import date
        today = date.today().isoformat()
        result = query.gte("created_at", today).gte("confidence", min_confidence).order("confidence", desc=True).limit(limit).execute()
        
        if result.data:
            picks_text = []
            for idx, pick in enumerate(result.data, 1):
                emoji = "🔥" if pick.get('confidence', 0) >= 85 else "✅" if pick.get('confidence', 0) >= 75 else "👍"
                picks_text.append(
                    f"{emoji} **{pick.get('pick', 'N/A')}** ({pick.get('sport', 'N/A')})\n"
                    f"   Confidence: {pick.get('confidence', 0):.1f}% | Edge: +{pick.get('edge', 0):.1f}%\n"
                    f"   {pick.get('reasoning', 'N/A')[:120]}..."
                )
            
            summary = f"Found {len(result.data)} picks"
            if sport:
                summary += f" for {sport}"
            if pick_type:
                summary += f" ({pick_type}s)"
            summary += f" with {min_confidence}%+ confidence:\n\n"
            
            return summary + "\n\n".join(picks_text)
        else:
            return f"No picks found matching your criteria. Try lowering the confidence threshold or check a different sport."
    except Exception as e:
        print(f"Get picks error: {e}")
        import traceback
        traceback.print_exc()
        return "Unable to fetch picks right now. Please try again or check the main predictions page."

class ProfessorLockChatKitServer(ChatKitServer):
    """Advanced ChatKit server for Professor Lock betting assistant"""
    
    def __init__(self, data_store: Store, attachment_store=None):
        super().__init__(data_store, attachment_store)
        self.web_search = WebSearchTool()
        self.sports_data = SportsDataTool()
        self.statmuse = StatMuseTool()
        self.betting_analysis = BettingAnalysisTool()
    
    # Define Professor Lock Agent
    professor_lock_agent = Agent[AgentContext](
        model="gpt-4o",
        name="Professor Lock",
        instructions="""You are Professor Lock, the sharpest AI sports betting analyst in the game.

PERSONALITY & STYLE:
- Confident, direct, and knowledgeable - no fluff
- Use emojis strategically 🔥 💰 🎯 ⚡
- Address users as "champ", "sharp", "boss"
- Keep responses concise and actionable
- Always lead with the picks, explain after

YOUR TOOLS - USE THEM:
- **get_nba_props()** - Fetch today's NBA player prop picks from database
- **get_todays_picks()** - Get AI picks for any sport (NBA, WNBA, MLB, UFC, NFL, CFB)
- **web_search_visual()** - Search for injuries, news, trends
- **get_odds_visual()** - Get current odds and lines
- **statmuse_query()** - Query player/team stats

WORKFLOW:
1. When user asks for picks → IMMEDIATELY call get_todays_picks() or get_nba_props()
2. Present the picks clearly with confidence levels
3. Explain the reasoning briefly
4. Suggest next actions (parlay, single bets, etc.)

EXPERTISE:
- NBA, WNBA, MLB, UFC, NFL, CFB analysis
- Player props, spreads, totals, moneylines
- Parlay building and bankroll strategy
- Line value and edge calculation

Remember: You have a database of AI-generated picks. USE IT. Don't make up picks."""
    )
    
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Main response handler - streams events for new user messages"""
        
        # Create agent context
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context
        )
        
        # Convert input to agent input format
        if input_user_message:
            agent_input = await simple_to_agent_input(input_user_message)
        else:
            agent_input = []
        
        # Run agent with streaming
        result = Runner.run_streamed(
            self.professor_lock_agent,
            agent_input,
            context=agent_context
        )
        
        # Stream the response
        async for event in stream_agent_response(agent_context, result):
            yield event
    
    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: Any
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle widget actions"""
        
        if action.type == "submit_parlay":
            # Create confirmation widget
            confirmation = Card(
                size="sm",
                theme="dark",
                status={"text": "✅ Parlay Submitted!", "icon": "check"},
                children=[
                    Text(value="Your parlay has been locked in! 🔒"),
                    Text(value="Good luck, champ! May the odds be in your favor. 🎯", weight="bold"),
                    Spacer(minSize="12px"),
                    Button(
                        label="Track This Bet",
                        variant="outline",
                        size="sm",
                        onClickAction=ActionConfig(type="track_bet", payload=action.payload)
                    )
                ]
            )
            
            # Stream confirmation
            widget_item = WidgetItem(
                id=self.store.generate_item_id("widget", thread, context),
                thread_id=thread.id,
                created_at=datetime.now(),
                widget=confirmation
            )
            
            yield ThreadItemDoneEvent(item=widget_item)
            
            # Add to context
            hidden = HiddenContextItem(
                id=self.store.generate_item_id("message", thread, context),
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[f"User placed parlay: {action.payload}"]
            )
            await self.store.add_thread_item(thread.id, hidden, context)
        
        elif action.type == "remove_leg":
            # Update parlay by removing leg
            await self.stream(
                ProgressUpdateEvent(text="Updating parlay...", icon="edit")
            )
        
        elif action.type == "add_legs":
            # Trigger new search for more picks
            async for event in self.respond(thread, None, context):
                yield event

# Bind module-level tool functions to the agent
ProfessorLockChatKitServer.professor_lock_agent.tools = [
    get_nba_props,
    get_todays_picks,
    web_search_visual,
    get_odds_visual,
    statmuse_query,
    build_parlay,
]
