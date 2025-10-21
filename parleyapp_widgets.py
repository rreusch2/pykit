"""
ParleyApp Custom Widgets for Professor Lock ChatKit
Advanced sports betting widgets with interactive elements
"""

from typing import Dict, Any, List, Optional
from chatkit.widgets import (
    Card, Text, Title, Button, Row, Col, Box, Markdown,
    ListView, ListViewItem, Badge, Icon, Divider, Spacer,
    Chart, Series, Image
)
from chatkit.actions import ActionConfig

def create_search_progress_widget(query: str, search_type: str = "general") -> Card:
    """Create live search progress widget"""
    
    search_icons = {
        "injury": "medical-cross",
        "weather": "cloud",
        "news": "newspaper",
        "general": "search"
    }
    
    return Card(
        size="md",
        theme="dark",
        children=[
            Row(align="center", gap="8px", children=[
                Icon(name=search_icons.get(search_type, "search"), size="md", color="#168aa2"),
                Title(value="🔍 Live Search", size="sm"),
                Spacer(),
                Badge(label="SEARCHING", color="warning", variant="soft", pill=True)
            ]),
            Divider(spacing="8px"),
            Text(
                value=f"Searching: {query}",
                italic=True,
                streaming=True
            ),
            Box(
                id="search_results",
                direction="column",
                gap="4px",
                children=[]
            )
        ]
    )

def create_odds_comparison_widget(games: List[Dict[str, Any]]) -> Card:
    """Create live odds comparison table"""
    
    odds_rows = []
    for idx, game in enumerate(games):
        odds_rows.append(
            ListViewItem(
                children=[
                    Row(gap="12px", align="center", children=[
                        Col(flex=3, children=[
                            Text(value=game["matchup"], weight="semibold", size="sm"),
                            Text(value=game.get("time", ""), size="xs", color="#888")
                        ]),
                        Col(flex=1, children=[
                            Badge(
                                label=str(game.get("spread", "N/A")), 
                                color="info", 
                                variant="soft",
                                size="sm"
                            )
                        ]),
                        Col(flex=1, children=[
                            Badge(
                                label=f"O/U {game.get('total', 'N/A')}", 
                                color="secondary", 
                                variant="soft",
                                size="sm"
                            )
                        ]),
                        Col(flex=2, children=[
                            Text(value=f"ML: {game.get('home_ml', 'N/A')}", size="xs"),
                            Text(value=f"ML: {game.get('away_ml', 'N/A')}", size="xs")
                        ]),
                        Button(
                            label="Analyze",
                            size="xs",
                            variant="outline",
                            onClickAction=ActionConfig(
                                type="analyze_game",
                                payload={"game": game, "index": idx}
                            )
                        )
                    ])
                ]
            )
        )
    
    return Card(
        size="full",
        children=[
            Row(align="center", gap="8px", children=[
                Icon(name="chart-line", size="md", color="#168aa2"),
                Title(value="📊 Live Odds Board", size="md"),
                Spacer(),
                Button(
                    label="Refresh",
                    size="sm",
                    variant="ghost",
                    onClickAction=ActionConfig(type="refresh_odds")
                )
            ]),
            Divider(spacing="8px"),
            ListView(children=odds_rows, limit=10)
        ]
    )

def create_parlay_builder_widget(legs: List[Dict[str, Any]], stake: float = 100) -> Card:
    """Create interactive parlay builder"""
    
    # Calculate total odds
    total_odds = 1.0
    for leg in legs:
        decimal_odds = _american_to_decimal(leg.get("odds", -110))
        total_odds *= decimal_odds
    
    potential_payout = stake * total_odds
    profit = potential_payout - stake
    
    # Create leg items
    leg_items = []
    for i, leg in enumerate(legs):
        confidence_color = "success" if leg.get("confidence", 0) >= 75 else "warning" if leg.get("confidence", 0) >= 60 else "danger"
        
        leg_items.append(
            ListViewItem(children=[
                Row(gap="8px", align="center", children=[
                    Badge(label=str(i+1), variant="solid", pill=True, size="sm", color="info"),
                    Col(flex=1, children=[
                        Text(value=leg["pick"], weight="semibold", size="sm"),
                        Text(value=f"{leg.get('match', '')} • {leg.get('odds', '')}", size="xs", color="#888")
                    ]),
                    Badge(
                        label=f"{leg.get('confidence', 0)}%", 
                        color=confidence_color, 
                        variant="soft",
                        size="sm"
                    ),
                    Button(
                        label="❌",
                        size="xs",
                        variant="ghost",
                        color="danger",
                        onClickAction=ActionConfig(
                            type="remove_parlay_leg",
                            payload={"index": i}
                        )
                    )
                ])
            ])
        )
    
    return Card(
        size="full",
        theme="dark",
        children=[
            # Header
            Row(align="center", gap="8px", children=[
                Icon(name="target", size="lg", color="#168aa2"),
                Title(value="🎯 Professor Lock's Parlay Builder", size="lg", weight="bold"),
            ]),
            Divider(spacing="12px"),
            
            # Legs section
            Box(
                padding="12px", 
                background="#0f1419", 
                radius="md", 
                children=[
                    Row(justify="between", align="center", children=[
                        Text(value=f"Parlay Legs ({len(legs)})", weight="semibold"),
                        Button(
                            label="+ Add Leg",
                            size="sm",
                            variant="outline",
                            onClickAction=ActionConfig(type="add_parlay_leg")
                        )
                    ]),
                    Spacer(minSize="8px"),
                    ListView(children=leg_items)
                ]
            ),
            
            Spacer(minSize="12px"),
            
            # Odds calculation
            Box(
                padding="12px",
                background="#1a1d2e",
                radius="md",
                border={"size": 1, "color": "#168aa2"},
                children=[
                    Row(justify="between", children=[
                        Text(value="Combined Odds:", weight="medium"),
                        Text(value=f"+{int((total_odds - 1) * 100)}", weight="bold", color="#10b981", size="lg")
                    ]),
                    Row(justify="between", children=[
                        Text(value="Risk Amount:", weight="medium"),
                        Text(value=f"${stake:.2f}", weight="medium")
                    ]),
                    Divider(spacing="8px"),
                    Row(justify="between", children=[
                        Text(value="Potential Payout:", weight="bold", size="lg"),
                        Text(value=f"${potential_payout:.2f}", weight="bold", size="lg", color="#10b981")
                    ]),
                    Row(justify="between", children=[
                        Text(value="Profit:", weight="medium"),
                        Text(value=f"${profit:.2f}", weight="medium", color="#10b981")
                    ])
                ]
            ),
            
            Spacer(minSize="16px"),
            
            # Action buttons
            Row(gap="12px", children=[
                Button(
                    label="🔒 Lock It In, Champ!",
                    style="primary",
                    size="lg",
                    block=True,
                    onClickAction=ActionConfig(
                        type="submit_parlay",
                        payload={
                            "legs": legs, 
                            "stake": stake,
                            "total_odds": total_odds,
                            "payout": potential_payout
                        }
                    )
                ),
                Button(
                    label="Clear All",
                    variant="outline",
                    color="danger",
                    size="lg",
                    onClickAction=ActionConfig(type="clear_parlay")
                )
            ])
        ]
    )

def create_trends_chart_widget(trends_data: Dict[str, Any]) -> Card:
    """Create performance trends chart"""
    
    # Convert trends to chart format
    chart_data = []
    for trend in trends_data.get("trends", []):
        chart_data.append({
            "date": trend["date"],
            "hit_rate": trend["hit_rate"],
            "roi": trend.get("roi", 0)
        })
    
    return Card(
        size="full",
        children=[
            Row(align="center", gap="8px", children=[
                Icon(name="trending-up", size="md", color="#10b981"),
                Title(value="📈 Performance Trends", size="md"),
                Spacer(),
                Badge(label="LAST 30 DAYS", color="info", variant="soft")
            ]),
            Divider(spacing="12px"),
            Chart(
                data=chart_data,
                series=[
                    Series(
                        key="hit_rate", 
                        name="Hit Rate %", 
                        color="#10b981",
                        type="line"
                    ),
                    Series(
                        key="roi", 
                        name="ROI %", 
                        color="#168aa2",
                        type="bar"
                    )
                ],
                xAxis="date",
                yAxis="hit_rate",
                showLegend=True,
                height="300px"
            ),
            Spacer(minSize="12px"),
            Row(gap="16px", justify="center", children=[
                Col(children=[
                    Text(value="Avg Hit Rate", weight="medium", textAlign="center"),
                    Text(value="67.8%", weight="bold", size="lg", color="#10b981", textAlign="center")
                ]),
                Col(children=[
                    Text(value="Total ROI", weight="medium", textAlign="center"),
                    Text(value="+23.4%", weight="bold", size="lg", color="#10b981", textAlign="center")
                ]),
                Col(children=[
                    Text(value="Best Streak", weight="medium", textAlign="center"),
                    Text(value="8W", weight="bold", size="lg", color="#10b981", textAlign="center")
                ])
            ])
        ]
    )

def create_player_prop_widget(prop_data: Dict[str, Any]) -> Card:
    """Create player prop analysis widget"""
    
    confidence = prop_data.get("confidence", 0)
    confidence_color = "#10b981" if confidence >= 75 else "#f59e0b" if confidence >= 60 else "#ef4444"
    
    return Card(
        size="md",
        children=[
            Row(align="center", gap="8px", children=[
                Icon(name="user", size="md", color="#168aa2"),
                Title(value="🏀 Player Prop Alert", size="sm"),
                Spacer(),
                Badge(
                    label=f"{confidence}%", 
                    color="success" if confidence >= 75 else "warning" if confidence >= 60 else "danger",
                    variant="solid"
                )
            ]),
            Divider(spacing="8px"),
            Col(gap="8px", children=[
                Text(value=prop_data.get("player_name", ""), weight="bold", size="lg"),
                Text(value=f"{prop_data.get('team', '')} vs {prop_data.get('opponent', '')}", color="#888"),
                Row(gap="12px", children=[
                    Text(value=prop_data.get("prop_type", ""), weight="medium"),
                    Text(value=prop_data.get("line", ""), weight="bold", color="#168aa2"),
                    Text(value=prop_data.get("odds", ""), weight="bold")
                ]),
                Box(
                    padding="8px",
                    background="#0f1419",
                    radius="md",
                    children=[
                        Text(value="💡 Analysis:", weight="medium", size="sm"),
                        Text(value=prop_data.get("reasoning", "Strong value based on recent trends"), size="sm")
                    ]
                ),
                Row(gap="8px", children=[
                    Button(
                        label="Add to Slip",
                        style="primary",
                        size="sm",
                        onClickAction=ActionConfig(
                            type="add_to_betslip",
                            payload=prop_data
                        )
                    ),
                    Button(
                        label="More Stats",
                        variant="outline",
                        size="sm",
                        onClickAction=ActionConfig(
                            type="view_player_stats",
                            payload={"player": prop_data.get("player_name")}
                        )
                    )
                ])
            ])
        ]
    )

def _american_to_decimal(odds: Any) -> float:
    """Convert American odds to decimal odds"""
    try:
        if isinstance(odds, str):
            odds = int(odds.replace("+", ""))
        
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1
    except:
        return 2.0  # Default to even odds
