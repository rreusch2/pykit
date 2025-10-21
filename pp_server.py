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
- Confident, sharp, and witty with gambling slang
- Use emojis strategically 🎯 💰 🔥 ⚡
- Address users as "champ", "sharp", "ace", "boss"
- Keep responses 2-3 sentences max unless doing analysis
- Bold all picks, odds, and key numbers
- End with specific action items

EXPERTISE:
- MLB, WNBA, UFC, NFL, CFB sports analysis
- Player props, spreads, totals, moneylines
- Parlay construction and bankroll management
- Real-time odds analysis and line movement
- Injury reports, weather impacts, lineup changes

VISUAL COMMUNICATION:
When analyzing, use widgets to show:
1. Live search progress with results
2. Odds comparison tables
3. Interactive parlay builders
4. Trend charts and analytics
5. Bet slip confirmations

Always provide value-driven picks with reasoning."""
    )
    
    @function_tool(description="Search web for sports news, injuries, weather, betting insights")
    async def web_search_visual(
        self,
        ctx: RunContextWrapper[AgentContext],
        query: str,
        search_type: str = "general"
    ) -> str:
        """Web search with live progress widget"""
        
        # Create and stream initial search widget
        search_widget = create_search_progress_widget(query, search_type)
        
        await ctx.context.stream_widget(search_widget)
        
        # Perform search and stream results
        results = []
        async for update in self.web_search.search_with_updates(query):
            if update["type"] == "result":
                # Add result to widget
                result_item = ListViewItem(children=[
                    Row(gap="8px", children=[
                        Icon(name="link", size="sm"),
                        Col(flex=1, children=[
                            Text(value=update["title"], weight="semibold", truncate=True),
                            Text(value=update["snippet"], size="sm", color="gray", maxLines=2),
                            Badge(label=update["source"], size="sm", variant="outline")
                        ])
                    ])
                ])
                
                # Update widget
                search_widget.children[2].children.append(result_item)
                await ctx.context.update_widget(search_widget)
                
                results.append(f"{update['title']}: {update['snippet']}")
        
        # Final status update
        search_widget.children[2].children[0].value = f"✅ Found {len(results)} results"
        await ctx.context.update_widget(search_widget)
        
        return "\n".join(results)
    
    @function_tool(description="Get live sports odds and player props with visualization")
    async def get_odds_visual(
        self,
        ctx: RunContextWrapper[AgentContext],
        sport: str,
        market_type: str = "all"  # all, spreads, totals, moneyline, props
    ) -> str:
        """Fetch and visualize odds data"""
        
        # Progress indicator
        await ctx.context.stream(
            ProgressUpdateEvent(text=f"📊 Loading {sport} odds...", icon="chart")
        )
        
        # Get odds data
        odds_data = await self.sports_data.get_odds(sport, market_type)
        
        # Create odds comparison widget using our custom widget
        odds_widget = create_odds_comparison_widget(odds_data.get("games", []))
        
        await ctx.context.stream_widget(odds_widget)
        
        return json.dumps(odds_data, indent=2)
    
    @function_tool(description="Query StatMuse for historical stats and trends")
    async def statmuse_query(
        self,
        ctx: RunContextWrapper[AgentContext],
        question: str
    ) -> str:
        """Query StatMuse with visual response"""
        
        # Show query progress
        await ctx.context.stream(
            ProgressUpdateEvent(text=f"📈 Querying StatMuse: {question}", icon="chart")
        )
        
        # Get StatMuse response
        result = await self.statmuse.query(question)
        
        # Create result widget
        result_widget = Card(
            size="md",
            background="#1a1d2e",
            children=[
                Row(gap="8px", align="center", children=[
                    Image(
                        src="https://www.statmuse.com/img/statmuse-logo.png",
                        alt="StatMuse",
                        height="24px",
                        width="auto"
                    ),
                    Title(value="StatMuse Result", size="sm")
                ]),
                Divider(spacing="8px"),
                Markdown(value=result.get("answer", ""), streaming=False),
                Box(padding="8px", background="#0f1419", radius="md", children=[
                    Text(value="📊 " + result.get("visual_context", ""), size="sm", color="#888")
                ])
            ]
        )
        
        await ctx.context.stream_widget(result_widget)
        
        return result.get("answer", "")
    
    @function_tool(description="Build interactive parlay with visual bet slip")
    async def build_parlay(
        self,
        ctx: RunContextWrapper[AgentContext],
        legs: List[Dict[str, Any]],
        stake: float = 100
    ) -> str:
        """Create interactive parlay builder"""
        
        # Calculate parlay odds
        total_odds = 1.0
        for leg in legs:
            decimal_odds = self._american_to_decimal(leg.get("odds", -110))
            total_odds *= decimal_odds
        
        payout = stake * total_odds
        profit = payout - stake
        
        # Create leg items
        leg_items = []
        for i, leg in enumerate(legs, 1):
            leg_items.append(
                ListViewItem(children=[
                    Row(gap="12px", align="center", children=[
                        Badge(label=str(i), variant="solid", pill=True, size="sm"),
                        Col(flex=1, children=[
                            Text(value=leg["pick"], weight="semibold"),
                            Text(value=f"{leg['type']} • {leg['odds']}", size="sm", color="gray")
                        ]),
                        Button(
                            label="❌",
                            size="sm",
                            variant="ghost",
                            onClickAction=ActionConfig(
                                type="remove_leg",
                                payload={"index": i-1}
                            )
                        )
                    ])
                ])
            )
        
        # Create parlay widget
        parlay_widget = Card(
            size="lg",
            theme="dark",
            asForm=True,
            children=[
                Title(value="🎯 Parlay Builder", size="lg", weight="bold"),
                Divider(spacing="12px"),
                
                # Legs section
                Box(padding="12px", background="#0f1419", radius="md", children=[
                    Text(value=f"Legs ({len(legs)})", weight="semibold"),
                    ListView(children=leg_items)
                ]),
                
                # Odds summary
                Box(padding="12px", margin="12px 0", children=[
                    Row(justify="between", children=[
                        Text(value="Parlay Odds:", weight="medium"),
                        Text(value=f"+{int((total_odds - 1) * 100)}", weight="bold", color="green")
                    ]),
                    Row(justify="between", children=[
                        Text(value="Stake:", weight="medium"),
                        Text(value=f"${stake:.2f}")
                    ]),
                    Divider(spacing="8px"),
                    Row(justify="between", children=[
                        Text(value="Potential Payout:", weight="bold", size="lg"),
                        Text(value=f"${payout:.2f}", weight="bold", size="lg", color="green")
                    ])
                ]),
                
                # Action buttons
                Row(gap="12px", children=[
                    Button(
                        label="🔒 Lock It In",
                        style="primary",
                        block=True,
                        onClickAction=ActionConfig(
                            type="submit_parlay",
                            payload={"legs": legs, "stake": stake}
                        )
                    ),
                    Button(
                        label="Add More Legs",
                        variant="outline",
                        block=True,
                        onClickAction=ActionConfig(type="add_legs")
                    )
                ])
            ],
            confirm={"label": "Place Bet", "action": ActionConfig(type="confirm_parlay")},
            cancel={"label": "Cancel", "action": ActionConfig(type="cancel_parlay")}
        )
        
        await ctx.context.stream_widget(parlay_widget)
        
        return f"Parlay created: {len(legs)} legs at +{int((total_odds - 1) * 100)} odds. Potential payout: ${payout:.2f}"
    
    def _american_to_decimal(self, odds: int) -> float:
        """Convert American odds to decimal"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1
    
    # Add tools to agent
    professor_lock_agent.tools = [
        web_search_visual,
        get_odds_visual,
        statmuse_query,
        build_parlay
    ]
    
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Main response handler"""
        
        # Create agent context
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context
        )
        
        # Run agent with streaming
        result = Runner.run_streamed(
            self.professor_lock_agent,
            await simple_to_agent_input(input_user_message) if input_user_message else [],
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
