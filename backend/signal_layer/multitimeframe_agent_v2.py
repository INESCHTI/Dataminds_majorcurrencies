"""
Multi-Timeframe Analysis Agent V2
Analyse technique sur court/moyen/long terme
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass

from agents.base_agent import BaseAgent, AgentOutput
from data_layer.timeseries_loader import TimeSeriesLoader


@dataclass
class TimeframeSignal:
    """Signal pour un timeframe spécifique"""
    timeframe: str
    signal: int  # -1, 0, 1
    confidence: float
    reasoning: str
    indicators: Dict


class MultitimeframeAgentV2(BaseAgent):
    """
    Agent d'analyse technique multi-échelle
    
    Timeframes:
    - Court terme (M1, M5, M15): Tactique
    - Moyen terme (H1, H4, D1): Stratégique  
    - Long terme (W1, MN1): Positionnel
    """
    
    AGENT_TYPE = 'multitimeframe'
    
    def __init__(self):
        super().__init__()
        self.timeframes = {
            'tactique': ['M1', 'M5', 'M15'],
            'strategique': ['H1', 'H4', 'D1'], 
            'positionnel': ['W1', 'MN1']
        }
        self.loader = TimeSeriesLoader()
    
    def generate_signal(self, symbol: str) -> Dict:
        """
        Génère signal multi-timeframe
        """
        try:
            # Récupérer tous les timeframes
            timeframe_signals = {}
            
            for category, tfs in self.timeframes.items():
                category_signals = []
                
                for tf in tfs:
                    try:
                        signal = self._analyze_timeframe(symbol, tf, category)
                        category_signals.append(signal)
                    except Exception as e:
                        print(f"Erreur analyse {tf}: {e}")
                        continue
                
                if category_signals:
                    # Agréger signaux par catégorie
                    timeframe_signals[category] = self._aggregate_category_signals(category_signals)
            
            # Générer signal final avec pondération
            final_signal = self._generate_multitimeframe_signal(timeframe_signals)
            
            return {
                'signal': final_signal['signal'],
                'confidence': final_signal['confidence'],
                'timeframe_signals': timeframe_signals,
                'reasoning': final_signal['reasoning'],
                'agent': 'MultitimeframeV2',
                'features_used': {
                    'tactique_weight': 0.4,
                    'strategique_weight': 0.4,
                    'positionnel_weight': 0.2
                }
            }
            
        except Exception as e:
            print(f"Erreur MultitimeframeAgent: {e}")
            return {
                'signal': 0,
                'confidence': 0.5,
                'reasoning': f'Erreur analyse multi-timeframe: {e}',
                'agent': 'MultitimeframeV2'
            }
    
    def _analyze_timeframe(self, symbol: str, timeframe: str, category: str) -> TimeframeSignal:
        """
        Analyse un timeframe spécifique
        """
        try:
            # Charger données
            df = self.loader.load_ohlcv(symbol, timeframe, limit=200)
            
            if df.empty:
                return TimeframeSignal(
                    timeframe=timeframe,
                    signal=0,
                    confidence=0.0,
                    reasoning=f'Pas de données pour {timeframe}',
                    indicators={}
                )
            
            # Calculer indicateurs techniques
            indicators = self._calculate_indicators(df)
            
            # Générer signal selon timeframe
            signal, confidence, reasoning = self._generate_timeframe_signal(
                indicators, timeframe, category
            )
            
            return TimeframeSignal(
                timeframe=timeframe,
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                indicators=indicators
            )
            
        except Exception as e:
            return TimeframeSignal(
                timeframe=timeframe,
                signal=0,
                confidence=0.0,
                reasoning=f'Erreur {timeframe}: {e}',
                indicators={}
            )
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calcule indicateurs techniques
        """
        try:
            import ta
            
            indicators = {}
            
            # Trend indicators
            indicators['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            indicators['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
            indicators['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
            indicators['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
            
            # Momentum indicators
            indicators['rsi'] = ta.momentum.rsi(df['close'], window=14)
            indicators['macd'] = ta.trend.macd(df['close'])
            indicators['stoch'] = ta.momentum.stoch(df['high'], df['low'], df['close'])
            
            # Volatility indicators
            indicators['bb'] = ta.volatility.bollinger_hband(df['close'])
            indicators['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
            
            # Volume indicators
            if 'volume' in df.columns:
                indicators['volume_sma'] = ta.volume.volume_sma(df['close'], df['volume'])
            
            return indicators
            
        except Exception as e:
            print(f"Erreur calculateurs indicateurs: {e}")
            return {}
    
    def _generate_timeframe_signal(self, indicators: Dict, timeframe: str, category: str) -> tuple:
        """
        Génère signal pour un timeframe
        """
        try:
            signal = 0
            confidence = 0.0
            reasoning_parts = []
            
            # Règles selon catégorie
            if category == 'tactique':
                # Court terme : RSI + MACD rapide
                rsi = indicators.get('rsi', [])
                macd = indicators.get('macd', pd.DataFrame())
                
                if len(rsi) > 0:
                    current_rsi = rsi.iloc[-1]
                    if current_rsi < 30:
                        signal = 1
                        confidence += 0.6
                        reasoning_parts.append(f"RSI surventu ({current_rsi:.1f})")
                    elif current_rsi > 70:
                        signal = -1
                        confidence += 0.6
                        reasoning_parts.append(f"RSI suracheté ({current_rsi:.1f})")
                
                if not macd.empty and 'macd' in macd.columns:
                    macd_line = macd['macd'].iloc[-1]
                    macd_signal = macd['macd_signal'].iloc[-1]
                    if macd_line > macd_signal:
                        signal = 1 if signal != -1 else signal
                        confidence += 0.4
                        reasoning_parts.append("MACD haussier")
                    else:
                        signal = -1 if signal != 1 else signal
                        confidence += 0.4
                        reasoning_parts.append("MACD baissier")
            
            elif category == 'strategique':
                # Moyen terme : SMA + Trend
                sma_20 = indicators.get('sma_20', [])
                sma_50 = indicators.get('sma_50', [])
                
                if len(sma_20) > 0 and len(sma_50) > 0:
                    current_price = indicators.get('close', pd.Series()).iloc[-1] if 'close' in indicators else None
                    current_sma20 = sma_20.iloc[-1]
                    current_sma50 = sma_50.iloc[-1]
                    
                    if current_price and current_sma20 > current_sma50:
                        signal = 1
                        confidence += 0.7
                        reasoning_parts.append(f"Trend haussier (SMA20>{SMA50})")
                    elif current_price and current_sma20 < current_sma50:
                        signal = -1
                        confidence += 0.7
                        reasoning_parts.append(f"Trend baissier (SMA20<{SMA50})")
            
            elif category == 'positionnel':
                # Long terme : Analyse structurelle
                bb = indicators.get('bb', [])
                
                if len(bb) > 0:
                    # Position relative aux bandes de Bollinger
                    current_price = indicators.get('close', pd.Series()).iloc[-1] if 'close' in indicators else None
                    bb_upper = bb.iloc[-1] if not bb.empty else None
                    
                    if current_price and bb_upper:
                        # Simplifié : utiliser ATR pour la volatilité
                        atr = indicators.get('atr', pd.Series())
                        if len(atr) > 0:
                            volatility = atr.iloc[-1]
                            if volatility > 0.002:  # haute volatilité
                                confidence = 0.3  # faible confiance en période volatile
                                reasoning_parts.append("Forte volatilité - signal positionnel faible")
                            else:
                                confidence = 0.8
                                reasoning_parts.append("Faible volatilité - signal positionnel fiable")
            
            # Limiter confiance
            confidence = min(confidence, 1.0)
            
            reasoning = f"{timeframe}: " + "; ".join(reasoning_parts) if reasoning_parts else f"{timeframe}: Neutre"
            
            return signal, confidence, reasoning
            
        except Exception as e:
            return 0, 0.0, f"Erreur signal {timeframe}: {e}"
    
    def _aggregate_category_signals(self, signals: List[TimeframeSignal]) -> Dict:
        """
        Agrège les signaux d'une catégorie
        """
        if not signals:
            return {'signal': 0, 'confidence': 0.0, 'reasoning': 'Pas de signaux'}
        
        # Pondération par confiance
        total_weight = sum(s.confidence for s in signals if s.confidence > 0)
        
        if total_weight == 0:
            return {'signal': 0, 'confidence': 0.0, 'reasoning': 'Pas de signaux valides'}
        
        weighted_signal = sum(s.signal * s.confidence for s in signals) / total_weight
        avg_confidence = total_weight / len(signals)
        
        # Conversion signal -1/0/1
        if weighted_signal > 0.3:
            final_signal = 1
        elif weighted_signal < -0.3:
            final_signal = -1
        else:
            final_signal = 0
        
        reasoning = "; ".join([s.reasoning for s in signals if s.confidence > 0.3])
        
        return {
            'signal': final_signal,
            'confidence': avg_confidence,
            'reasoning': reasoning,
            'individual_signals': [s for s in signals if s.confidence > 0.3]
        }
    
    def _generate_multitimeframe_signal(self, timeframe_signals: Dict) -> Dict:
        """
        Génère signal final multi-timeframe
        """
        try:
            # Pondération par catégorie
            weights = {
                'tactique': 0.4,      # Court terme
                'strategique': 0.4,     # Moyen terme  
                'positionnel': 0.2      # Long terme
            }
            
            weighted_signal = 0
            total_confidence = 0
            active_categories = 0
            
            reasoning_parts = []
            
            for category, weight in weights.items():
                if category in timeframe_signals:
                    cat_signal = timeframe_signals[category]
                    signal_strength = cat_signal['signal']
                    confidence = cat_signal['confidence']
                    
                    weighted_signal += signal_strength * weight * confidence
                    total_confidence += confidence * weight
                    active_categories += 1
                    
                    reasoning_parts.append(
                        f"{category.title()}: {signal_strength} (conf: {confidence:.0%})"
                    )
            
            # Normaliser
            if active_categories > 0:
                final_signal = weighted_signal / max(total_confidence, 0.1)
                final_confidence = total_confidence
            else:
                final_signal = 0
                final_confidence = 0.0
            
            # Conversion finale
            if final_signal > 0.2:
                final_direction = 1
            elif final_signal < -0.2:
                final_direction = -1
            else:
                final_direction = 0
            
            reasoning = "Analyse multi-timeframe: " + "; ".join(reasoning_parts)
            
            return {
                'signal': final_direction,
                'confidence': min(final_confidence, 1.0),
                'reasoning': reasoning,
                'weighted_score': final_signal
            }
            
        except Exception as e:
            return {
                'signal': 0,
                'confidence': 0.0,
                'reasoning': f'Erreur agrégation multi-timeframe: {e}',
                'weighted_score': 0.0
            }
