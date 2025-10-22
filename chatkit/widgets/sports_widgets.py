"""
ChatKit Sports Betting Widgets
Custom widgets for the Professor Lock sports betting assistant
"""

from typing import List, Dict, Any, Optional, Literal

class SportsWidgets:
    """Factory class for creating sports betting widgets"""
    
    @staticmethod
    def search_progress(
        status: Literal['searching', 'analyzing', 'complete'] = 'searching',
        current_search: Optional[str] = None,
        sources: Optional[List[str]] = None,
        progress: int = 0
    ) -> Dict[str, Any]:
        """Create a search progress widget"""
        status_config = {
            'searching': {'icon': '🔍', 'text': 'Searching for data...', 'color': '#3B82F6'},
            'analyzing': {'icon': '🤔', 'text': 'Analyzing results...', 'color': '#F59E0B'},
            'complete': {'icon': '✅', 'text': 'Search complete!', 'color': '#10B981'}
        }
        
        config = status_config[status]
        sources = sources or []
        
        widget = {
            'type': 'Card',
            'size': 'md',
            'theme': 'dark',
            'children': [
                {
                    'type': 'Row',
                    'gap': 12,
                    'align': 'center',
                    'children': [
                        {'type': 'Text', 'value': config['icon'], 'size': 'xl'},
                        {
                            'type': 'Col',
                            'flex': 1,
                            'gap': 4,
                            'children': [
                                {'type': 'Text', 'value': config['text'], 'weight': 'semibold', 'color': config['color']}
                            ]
                        }
                    ]
                }
            ]
        }
        
        if current_search:
            widget['children'][0]['children'][1]['children'].append({
                'type': 'Text', 'value': current_search, 'size': 'sm', 'color': '#9CA3AF', 'truncate': True
            })
        
        if progress > 0:
            widget['children'].append({
                'type': 'Box', 'height': 4, 'background': '#374151', 'radius': 'full',
                'children': [{'type': 'Box', 'height': 4, 'width': f'{progress}%', 'background': config['color'], 'radius': 'full'}]
            })
        
        if sources:
            widget['children'].append({
                'type': 'Row', 'gap': 8,
                'children': [{'type': 'Badge', 'label': src, 'size': 'sm', 'variant': 'soft', 'color': 'info'} for src in sources]
            })
        
        return widget
    
    @staticmethod
    def parlay_builder(picks: List[Dict], total_odds: str = '+0', stake: float = 10) -> Dict[str, Any]:
        """Create a parlay builder widget"""
        selected = [p for p in picks if p.get('selected', False)]
        
        widget = {
            'type': 'Card',
            'size': 'lg',
            'theme': 'dark',
            'children': [
                {
                    'type': 'Row',
                    'justify': 'between',
                    'children': [
                        {'type': 'Title', 'value': '🎯 Parlay Builder', 'size': 'lg', 'weight': 'bold'}
                    ]
                }
            ]
        }
        
        if selected:
            widget['children'][0]['children'].append(
                {'type': 'Badge', 'label': f'{len(selected)} picks', 'color': 'success'}
            )
        
        pick_cards = []
        for pick in picks:
            is_sel = pick.get('selected', False)
            pick_cards.append({
                'type': 'Box',
                'padding': 12,
                'background': '#1E3A5F' if is_sel else '#1F2937',
                'radius': 'md',
                'border': {'size': 2 if is_sel else 1, 'color': '#3B82F6' if is_sel else '#374151'},
                'children': [{
                    'type': 'Row',
                    'justify': 'between',
                    'children': [
                        {
                            'type': 'Col',
                            'children': [
                                {'type': 'Text', 'value': pick['team'], 'weight': 'semibold'},
                                {'type': 'Text', 'value': pick['bet'], 'size': 'sm', 'color': '#9CA3AF'}
                            ]
                        },
                        {
                            'type': 'Col',
                            'children': [
                                {'type': 'Text', 'value': pick['odds'], 'weight': 'bold', 'color': '#10B981'},
                                {'type': 'Button', 'label': 'Remove' if is_sel else 'Add', 'size': 'xs',
                                 'variant': 'outline' if is_sel else 'solid', 'color': 'danger' if is_sel else 'primary',
                                 'onClickAction': {'type': 'toggle_parlay_pick', 'pickId': pick['id']}}
                            ]
                        }
                    ]
                }]
            })
        
        widget['children'].append({'type': 'Col', 'gap': 8, 'children': pick_cards})
        
        if selected:
            widget['children'].extend([
                {
                    'type': 'Box',
                    'padding': 12,
                    'background': '#1E293B',
                    'children': [{
                        'type': 'Col',
                        'gap': 8,
                        'children': [
                            {'type': 'Row', 'justify': 'between', 'children': [
                                {'type': 'Text', 'value': 'Total Odds:', 'color': '#9CA3AF'},
                                {'type': 'Text', 'value': total_odds, 'weight': 'bold', 'color': '#F59E0B'}
                            ]},
                            {'type': 'Row', 'justify': 'between', 'children': [
                                {'type': 'Text', 'value': 'Potential:', 'weight': 'semibold'},
                                {'type': 'Text', 'value': f'${stake * 2.5:.2f}', 'size': 'lg', 'weight': 'bold', 'color': '#10B981'}
                            ]}
                        ]
                    }]
                },
                {
                    'type': 'Button',
                    'label': 'Place Parlay',
                    'style': 'primary',
                    'block': True,
                    'onClickAction': {'type': 'place_parlay', 'picks': [p['id'] for p in selected]}
                }
            ])
        
        return widget
    
    @staticmethod
    def odds_table(title: str, team1: str, team2: str, odds: List[Dict]) -> Dict[str, Any]:
        """Create an odds comparison table"""
        return {
            'type': 'Card',
            'size': 'full',
            'theme': 'dark',
            'children': [
                {'type': 'Title', 'value': title, 'size': 'lg', 'weight': 'bold'},
                {
                    'type': 'Col',
                    'children': [
                        {
                            'type': 'Row',
                            'padding': 8,
                            'background': '#1E293B' if i % 2 == 0 else 'transparent',
                            'children': [
                                {'type': 'Text', 'value': row['book'], 'width': '25%'},
                                {'type': 'Badge', 'label': row['team1Odds'], 'color': 'info', 'size': 'sm'},
                                {'type': 'Badge', 'label': row['team2Odds'], 'color': 'info', 'size': 'sm'},
                                {'type': 'Text', 'value': row.get('overUnder', '-'), 'width': '25%'}
                            ]
                        } for i, row in enumerate(odds)
                    ]
                }
            ]
        }
    
    @staticmethod
    def player_card(name: str, team: str, position: str, stats: List[Dict], props: List[Dict] = None) -> Dict[str, Any]:
        """Create a player card widget"""
        widget = {
            'type': 'Card',
            'size': 'lg',
            'theme': 'dark',
            'children': [
                {
                    'type': 'Row',
                    'children': [
                        {
                            'type': 'Col',
                            'children': [
                                {'type': 'Title', 'value': name, 'size': 'xl', 'weight': 'bold'},
                                {
                                    'type': 'Row',
                                    'gap': 8,
                                    'children': [
                                        {'type': 'Badge', 'label': team, 'color': 'info'},
                                        {'type': 'Badge', 'label': position, 'color': 'secondary'}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    'type': 'Row',
                    'gap': 12,
                    'children': [
                        {
                            'type': 'Box',
                            'padding': 8,
                            'background': '#1E293B',
                            'children': [{
                                'type': 'Col',
                                'align': 'center',
                                'children': [
                                    {'type': 'Caption', 'value': stat['label'], 'color': '#94A3B8'},
                                    {'type': 'Text', 'value': stat['value'], 'weight': 'bold', 'size': 'lg'}
                                ]
                            }]
                        } for stat in stats
                    ]
                }
            ]
        }
        
        if props:
            prop_widgets = []
            for prop in props:
                prop_widgets.append({
                    'type': 'Box',
                    'padding': 12,
                    'background': '#1E293B',
                    'children': [{
                        'type': 'Row',
                        'justify': 'between',
                        'children': [
                            {'type': 'Text', 'value': prop['market'], 'weight': 'semibold'},
                            {
                                'type': 'Row',
                                'gap': 8,
                                'children': [
                                    {'type': 'Button', 'label': f"O {prop['over']}", 'size': 'sm',
                                     'onClickAction': {'type': 'select_prop', 'player': name, 'market': prop['market'], 'selection': 'over'}},
                                    {'type': 'Button', 'label': f"U {prop['under']}", 'size': 'sm',
                                     'onClickAction': {'type': 'select_prop', 'player': name, 'market': prop['market'], 'selection': 'under'}}
                                ]
                            }
                        ]
                    }]
                })
            widget['children'].append({'type': 'Col', 'gap': 8, 'children': prop_widgets})
        
        return widget
    
    @staticmethod
    def insights(insights: List[Dict], title: str = '💡 Key Insights') -> Dict[str, Any]:
        """Create a betting insights widget"""
        return {
            'type': 'Card',
            'size': 'md',
            'theme': 'dark',
            'children': [
                {'type': 'Title', 'value': title, 'size': 'lg', 'weight': 'bold'},
                {
                    'type': 'Col',
                    'gap': 12,
                    'children': [
                        {
                            'type': 'Box',
                            'padding': 12,
                            'background': '#1E293B',
                            'children': [{
                                'type': 'Row',
                                'gap': 12,
                                'children': [
                                    {'type': 'Text', 'value': ins.get('icon', '💡'), 'size': 'xl'},
                                    {
                                        'type': 'Col',
                                        'flex': 1,
                                        'children': [
                                            {
                                                'type': 'Row',
                                                'justify': 'between',
                                                'children': [
                                                    {'type': 'Text', 'value': ins['title'], 'weight': 'semibold'},
                                                    {'type': 'Badge', 'label': f"{ins['confidence']}%", 'color': 'success', 'size': 'sm'} if 'confidence' in ins else {}
                                                ]
                                            },
                                            {'type': 'Text', 'value': ins['description'], 'size': 'sm', 'color': '#94A3B8'}
                                        ]
                                    }
                                ]
                            }]
                        } for ins in insights
                    ]
                }
            ]
        }
