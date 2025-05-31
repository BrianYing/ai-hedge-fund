{
    'decisions': {
        'NVDA': {
            'action': 'hold', 
            'quantity': 0, 
            'confidence': 0.0, 
            'reasoning': 'Conflicting signals from technical analyst (bullish, 27) and sentiment agent (bearish, 51.35), no clear direction to take a position.'
        }
    }, 
    'analyst_signals': {
        'technical_analyst_agent': {
            'NVDA': {
                'signal': 'bullish', 
                'confidence': 27, 
                'strategy_signals': {
                    'trend_following': {
                        'signal': 'bullish', 
                        'confidence': 56, 
                        'metrics': {
                            'adx': 55.529802335489364, 
                            'trend_strength': 0.5552980233548936
                        }
                    }, 
                    'mean_reversion': {
                        'signal': 'neutral', 
                        'confidence': 50, 
                        'metrics': {
                            'z_score': 1.7327786985328075, 
                            'price_vs_bb': 0.770262536610404, 
                            'rsi_14': 79.5236791678073, 
                            'rsi_28': 82.07796241652433
                        }
                    }, 
                    'momentum': {
                        'signal': 'neutral', 
                        'confidence': 50, 
                        'metrics': {
                            'momentum_1m': 0.24457785783339547, 
                            'momentum_3m': 0.0, 
                            'momentum_6m': 0.0, 
                            'volume_momentum': 0.0035401002721131944
                        }
                    }, 
                    'volatility': {
                        'signal': 'neutral', 
                        'confidence': 50, 
                        'metrics': {
                            'historical_volatility': 0.3582083482040754, 
                            'volatility_regime': 0.0, 
                            'volatility_z_score': 0.0, 
                            'atr_ratio': 0.032618806457614155
                        }
                    }, 
                    'statistical_arbitrage': {
                        'signal': 'neutral', 
                        'confidence': 50, 
                        'metrics': {
                            'hurst_exponent': -5.100188179795765e-15, 
                            'skewness': 0.0, 
                            'kurtosis': 0.0
                        }
                    }
                }
            }
        }, 
        'sentiment_agent': {
            'NVDA': {
                'signal': 'bearish', 
                'confidence': 51.35, 
                'reasoning': 'Weighted Bullish signals: 164.6, Weighted Bearish signals: 190.0'
            }
        }, 
        'risk_management_agent': {
            'NVDA': {
                'remaining_position_limit': 20000.0, 
                'current_price': 139.19, 
                'reasoning': {
                    'portfolio_value': 100000.0, 
                    'current_position_value': 0.0, 
                    'position_limit': 20000.0, 
                    'remaining_limit': 20000.0, 
                    'available_cash': 100000.0
                }
            }
        }
    }
}