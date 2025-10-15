"""
ParleyApp ChatKit Widgets
Custom widgets for sports betting visualization
"""

from typing import List, Dict, Any
from chatkit.widgets import (
    Card, Text, Title, Button, Row, Col, Box, Markdown,
    ListView, ListViewItem, Badge, Icon, Divider, Spacer,
    Chart, Series, Form, Select, SelectOption, Input,
    Image, Transition
)

def create_search_progress_widget(query: str, search_type: str = "general") -> Card:
    """Create search progress widget"""
    
    search_icons = {
        "general": "search",
        "injury": "alert-circle", 
        "weather": "cloud",
        "news": "newspaper",
        "odds": "trending-up"
    }
    
    search_colors = {
        "general": "#168aa2",
        "injury": "#ef4444",
        "weather": "#6b7280",
        "news": "#10b981",
        "odds": "#8b5cf6"
    }
    
    return Card(
        size="md",
        theme="dark",
        background="#0f1419",
        padding="16px",
        radius="lg",
        children=[
            Row(align="center", gap="12px", children=[
                Icon(
                    name=search_icons.get(search_type, "search"),
                    size="lg",
                    color=search_colors.get(search_type, "#168aa2")
                ),
                Col(flex=1, children=[
                    Title(value=f"🔍 Searching", size="sm", weight="bold"),
                    Text(value=query, size="sm", color="#888", truncate=True)
                ]),
                Badge(
                    label="LIVE",
                    color="danger",
                    variant="soft",
                    pill=True,
                    size="sm"
                )
            ]),
            Divider(spacing="12px", color="#1f2937"),
            Box(
                id="search-results",
                direction="col",
                gap="8px",
                minHeight="60px",
                children=[
                    Text(
                        id="status",
                        value="Scanning sources...",
                        streaming=True,
                        italic=True,
                        color="#888",
                        size="sm"
                    )
                ]
            )
        ]
    )

def create_odds_comparison_widget(odds_data: Dict[str, Any]) -> Card:
    """Create odds comparison table"""
    
    rows = []
    for game in odds_data.get("games", [])[:10]:
        rows.append(
            ListViewItem(children=[
                Box(
                    padding="12px",
                    background="#1a1d2e",
                    radius="md",
                    margin="4px 0",
                    children=[
                        Row(gap="16px", align="center", children=[
                            # Teams
                            Col(flex=3, children=[
                                Text(value=game["away"], weight="semibold"),
                                Text(value="@", color="#666", size="sm"),
                                Text(value=game["home"], weight="semibold")
                            ]),
                            
                            # Spread
                            Col(align="center", children=[
                                Badge(
                                    label="SPREAD",
                                    size="sm",
                                    color="secondary",
                                    variant="outline"
                                ),
                                Text(value=game.get("spread", "N/A"), weight="bold")
                            ]),
                            
                            # Total
                            Col(align="center", children=[
                                Badge(
                                    label="O/U",
                                    size="sm",
                                    color="info",
                                    variant="outline"
                                ),
                                Text(value=game.get("total", "N/A"), weight="bold")
                            ]),
                            
                            # Moneyline
                            Col(align="end", children=[
                                Text(value=game.get("away_ml", "N/A"), size="sm"),
                                Text(value=game.get("home_ml", "N/A"), size="sm")
                            ])
                        ])
                    ]
                )
            ])
        )
    
    return Card(
        size="lg",
        theme="dark",
        children=[
            Row(align="center", justify="between", children=[
                Title(value="📊 Live Odds Board", size="md", weight="bold"),
                Badge(
                    label=f"{len(rows)} Games",
                    color="success",
                    variant="soft"
                )
            ]),
            Text(
                value=f"Last Update: {odds_data.get('timestamp', 'Just now')}",
                size="sm",
                color="#888"
            ),
            Divider(spacing="12px"),
            ListView(children=rows, limit="auto")
        ]
    )

def create_parlay_builder_widget(
    legs: List[Dict[str, Any]], 
    stake: float = 100
) -> Card:
    """Create interactive parlay builder"""
    
    # Calculate parlay math
    total_odds = 1.0
    for leg in legs:
        odds = leg.get("odds", -110)
        if odds > 0:
            decimal = (odds / 100) + 1
        else:
            decimal = (100 / abs(odds)) + 1
        total_odds *= decimal
    
    american_odds = int((total_odds - 1) * 100) if total_odds > 2 else int(-100 / (total_odds - 1))
    payout = stake * total_odds
    profit = payout - stake
    
    # Create leg items
    leg_items = []
    for i, leg in enumerate(legs, 1):
        confidence_color = {
            "MAX": "danger",
            "HIGH": "warning",
            "SOLID": "success",
            "DECENT": "info",
            "LOW": "secondary"
        }.get(leg.get("confidence", "SOLID"), "secondary")
        
        leg_items.append(
            ListViewItem(children=[
                Box(
                    padding="12px",
                    background="#1a1d2e",
                    radius="md",
                    margin="4px 0",
                    children=[
                        Row(gap="12px", align="center", children=[
                            Badge(
                                label=f"#{i}",
                                variant="solid",
                                color="primary",
                                pill=True,
                                size="sm"
                            ),
                            Col(flex=1, children=[
                                Text(value=leg["pick"], weight="semibold"),
                                Row(gap="8px", children=[
                                    Badge(
                                        label=leg["type"],
                                        size="sm",
                                        variant="outline"
                                    ),
                                    Text(
                                        value=f"@ {leg['odds']}",
                                        size="sm",
                                        weight="medium"
                                    ),
                                    Badge(
                                        label=leg.get("confidence", ""),
                                        size="sm",
                                        color=confidence_color,
                                        variant="soft"
                                    )
                                ])
                            ])
                        ])
                    ]
                )
            ])
        )
    
    return Card(
        size="lg",
        theme="dark",
        background="#0f1419",
        children=[
            # Header
            Row(align="center", justify="between", children=[
                Title(value="🎯 Parlay Builder", size="lg", weight="bold"),
                Badge(
                    label=f"{len(legs)}-Leg",
                    color="primary",
                    variant="solid",
                    size="lg"
                )
            ]),
            
            Divider(spacing="16px"),
            
            # Legs
            Box(
                padding="8px",
                background="#1a1d2e",
                radius="lg",
                children=[
                    Text(value="Your Picks", weight="semibold", margin="0 0 8px 0"),
                    ListView(children=leg_items)
                ]
            ),
            
            # Odds Summary
            Box(
                padding="16px",
                background="#1a1d2e",
                radius="lg",
                margin="16px 0",
                children=[
                    Row(justify="between", margin="8px 0", children=[
                        Text(value="Parlay Odds:", weight="medium"),
                        Text(
                            value=f"{'+' if american_odds > 0 else ''}{american_odds}",
                            weight="bold",
                            size="lg",
                            color="#10b981"
                        )
                    ]),
                    Row(justify="between", margin="8px 0", children=[
                        Text(value="Your Stake:", weight="medium"),
                        Input(
                            name="stake",
                            defaultValue=str(stake),
                            variant="outline",
                            size="sm",
                            inputType="number"
                        )
                    ]),
                    Divider(spacing="8px", color="#374151"),
                    Row(justify="between", margin="8px 0", children=[
                        Col(children=[
                            Text(value="To Win:", size="sm", color="#888"),
                            Text(value=f"${profit:.2f}", weight="bold", color="#10b981")
                        ]),
                        Col(align="end", children=[
                            Text(value="Total Payout:", size="sm", color="#888"),
                            Text(value=f"${payout:.2f}", weight="bold", size="lg", color="#10b981")
                        ])
                    ])
                ]
            ),
            
            # Actions
            Row(gap="12px", children=[
                Button(
                    label="🔒 Lock It In",
                    style="primary",
                    size="lg",
                    block=True,
                    pill=True
                ),
                Button(
                    label="Add More",
                    variant="outline",
                    size="lg",
                    block=True,
                    pill=True
                )
            ])
        ]
    )

def create_trends_chart_widget(trends_data: Dict[str, Any]) -> Card:
    """Create trends visualization"""
    
    # Format data for chart
    chart_data = []
    for point in trends_data.get("data", []):
        chart_data.append({
            "date": point["date"],
            "value": point["value"],
            "line": point.get("line", 0)
        })
    
    return Card(
        size="full",
        theme="dark",
        children=[
            Title(value="📈 Performance Trends", size="md", weight="bold"),
            Text(value=trends_data.get("description", ""), size="sm", color="#888"),
            Divider(spacing="12px"),
            Chart(
                data=chart_data,
                series=[
                    Series(
                        key="value",
                        name="Hit Rate",
                        color="#10b981",
                        type="line"
                    ),
                    Series(
                        key="line",
                        name="Prop Line",
                        color="#3b82f6",
                        type="bar"
                    )
                ],
                xAxis="date",
                showYAxis=True,
                showLegend=True,
                showTooltip=True,
                height="300px"
            )
        ]
    )

def create_bet_confirmation_widget(
    bet_type: str,
    details: Dict[str, Any],
    status: str = "pending"
) -> Card:
    """Create bet confirmation widget"""
    
    status_config = {
        "pending": {"icon": "clock", "color": "warning", "text": "Processing..."},
        "confirmed": {"icon": "check", "color": "success", "text": "Bet Placed!"},
        "failed": {"icon": "x", "color": "danger", "text": "Failed"}
    }
    
    config = status_config.get(status, status_config["pending"])
    
    return Card(
        size="sm",
        theme="dark",
        status={
            "text": config["text"],
            "icon": config["icon"]
        },
        background="#0f1419",
        children=[
            Row(align="center", gap="12px", children=[
                Icon(
                    name=config["icon"],
                    size="xl",
                    color=config["color"]
                ),
                Col(flex=1, children=[
                    Title(value=f"✅ {bet_type} Confirmed", size="md", weight="bold"),
                    Text(value=details.get("summary", ""), size="sm"),
                    Text(
                        value=f"Tracking ID: {details.get('id', 'N/A')}",
                        size="xs",
                        color="#666"
                    )
                ])
            ]),
            Spacer(minSize="16px"),
            Button(
                label="View in Bet Tracker",
                variant="outline",
                size="sm",
                block=True
            )
        ]
    )
