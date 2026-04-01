"""
LLM Integration for Central Bank Analysis
Uses GPT-4 to analyze central bank communications and policy decisions
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
import re

logger = logging.getLogger(__name__)

@dataclass
class CentralBankStatement:
    bank: str
    timestamp: datetime
    statement: str
    source: str
    statement_type: str  # "meeting", "press_release", "speech", "minutes"
    officials: List[str]

@dataclass
class LLMAnalysisResult:
    bank: str
    timestamp: datetime
    policy_bias: str  # "HAWKISH", "DOVISH", "NEUTRAL"
    confidence: float
    key_points: List[str]
    rate_outlook: str  # "RATE_UP", "RATE_DOWN", "RATE_HOLD"
    inflation_outlook: str  # "INFLATION_HIGH", "INFLATION_MODERATE", "INFLATION_LOW"
    economic_outlook: str  # "STRONG", "MODERATE", "WEAK"
    market_impact: str  # "BULLISH", "BEARISH", "NEUTRAL"
    reasoning: str
    raw_response: str

class LLMCentralBankAnalyzer:
    """Advanced LLM-powered central bank communication analyzer"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        # Central bank configurations
        self.bank_configs = {
            'FED': {
                'name': 'Federal Reserve',
                'currency': 'USD',
                'key_officials': ['Jerome Powell', 'Michelle Bowman', 'Michael Barr'],
                'meeting_schedule': 'Every 6 weeks',
                'time_zone': 'EST'
            },
            'ECB': {
                'name': 'European Central Bank',
                'currency': 'EUR',
                'key_officials': ['Christine Lagarde', 'Luis de Guindos', 'Frank Elderson'],
                'meeting_schedule': 'Every 6 weeks',
                'time_zone': 'CET'
            },
            'BOE': {
                'name': 'Bank of England',
                'currency': 'GBP',
                'key_officials': ['Andrew Bailey', 'Dave Ramsden', 'Ben Broadbent'],
                'meeting_schedule': 'Every 6 weeks',
                'time_zone': 'GMT'
            },
            'BOJ': {
                'name': 'Bank of Japan',
                'currency': 'JPY',
                'key_officials': ['Kazuo Ueda', 'Masayoshi Amamiya', 'Ryozo Himino'],
                'meeting_schedule': 'Every 6 weeks',
                'time_zone': 'JST'
            }
        }
        
        # Analysis prompts
        self.analysis_prompt = """
        You are an expert central bank analyst specializing in monetary policy analysis. 
        Analyze the following central bank communication and provide a comprehensive assessment.

        Central Bank: {bank}
        Statement Type: {statement_type}
        Date: {timestamp}
        Statement: {statement}

        Please analyze this communication and provide:
        1. Policy Bias (HAWKISH/DOVISH/NEUTRAL) - 0-100 confidence
        2. Rate Outlook (RATE_UP/RATE_DOWN/RATE_HOLD) 
        3. Inflation Outlook (INFLATION_HIGH/INFLATION_MODERATE/INFLATION_LOW)
        4. Economic Outlook (STRONG/MODERATE/WEAK)
        5. Market Impact (BULLISH/BEARISH/NEUTRAL)
        6. Key Points (3-5 bullet points)
        7. Detailed Reasoning

        Format your response as JSON:
        {{
            "policy_bias": "HAWKISH|DOVISH|NEUTRAL",
            "confidence": 0.0-1.0,
            "rate_outlook": "RATE_UP|RATE_DOWN|RATE_HOLD",
            "inflation_outlook": "INFLATION_HIGH|INFLATION_MODERATE|INFLATION_LOW",
            "economic_outlook": "STRONG|MODERATE|WEAK",
            "market_impact": "BULLISH|BEARISH|NEUTRAL",
            "key_points": ["point1", "point2", "point3"],
            "reasoning": "detailed explanation"
        }}
        """
    
    def analyze_statement(self, statement: CentralBankStatement) -> Optional[LLMAnalysisResult]:
        """Analyze a central bank statement using LLM"""
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not configured, using mock analysis")
                return self._mock_analysis(statement)
            
            # Prepare prompt
            prompt = self.analysis_prompt.format(
                bank=statement.bank,
                statement_type=statement.statement_type,
                timestamp=statement.timestamp.strftime('%Y-%m-%d'),
                statement=statement.statement[:4000]  # Limit to 4000 chars
            )
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert central bank analyst. Always respond with valid JSON.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 1000
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                logger.error(f"Could not extract JSON from LLM response: {content}")
                return self._mock_analysis(statement)
            
            # Create analysis result
            return LLMAnalysisResult(
                bank=statement.bank,
                timestamp=statement.timestamp,
                policy_bias=analysis_data['policy_bias'],
                confidence=analysis_data['confidence'],
                key_points=analysis_data['key_points'],
                rate_outlook=analysis_data['rate_outlook'],
                inflation_outlook=analysis_data['inflation_outlook'],
                economic_outlook=analysis_data['economic_outlook'],
                market_impact=analysis_data['market_impact'],
                reasoning=analysis_data['reasoning'],
                raw_response=content
            )
            
        except Exception as e:
            logger.error(f"Error analyzing statement with LLM: {e}")
            return self._mock_analysis(statement)
    
    def _mock_analysis(self, statement: CentralBankStatement) -> LLMAnalysisResult:
        """Mock analysis when LLM is not available"""
        import random
        
        # Simple keyword-based mock analysis
        hawkish_keywords = ['inflation', 'tighten', 'hike', 'restrictive', 'strong']
        dovish_keywords = ['patient', 'support', 'accommodative', 'concern', 'slow']
        
        statement_lower = statement.statement.lower()
        hawkish_score = sum(1 for word in hawkish_keywords if word in statement_lower)
        dovish_score = sum(1 for word in dovish_keywords if word in statement_lower)
        
        if hawkish_score > dovish_score:
            policy_bias = "HAWKISH"
            market_impact = "BULLISH"
            rate_outlook = "RATE_UP"
        elif dovish_score > hawkish_score:
            policy_bias = "DOVISH"
            market_impact = "BEARISH"
            rate_outlook = "RATE_DOWN"
        else:
            policy_bias = "NEUTRAL"
            market_impact = "NEUTRAL"
            rate_outlook = "RATE_HOLD"
        
        return LLMAnalysisResult(
            bank=statement.bank,
            timestamp=statement.timestamp,
            policy_bias=policy_bias,
            confidence=0.7,
            key_points=[
                f"Analysis based on {statement.statement_type}",
                f"Policy stance appears {policy_bias.lower()}",
                f"Market impact expected to be {market_impact.lower()}"
            ],
            rate_outlook=rate_outlook,
            inflation_outlook="INFLATION_MODERATE",
            economic_outlook="MODERATE",
            market_impact=market_impact,
            reasoning=f"Mock analysis based on keyword detection. Hawkish score: {hawkish_score}, Dovish score: {dovish_score}",
            raw_response="Mock analysis (LLM not available)"
        )
    
    def analyze_multiple_statements(self, statements: List[CentralBankStatement]) -> List[LLMAnalysisResult]:
        """Analyze multiple statements"""
        results = []
        for statement in statements:
            result = self.analyze_statement(statement)
            if result:
                results.append(result)
        return results
    
    def get_currency_impact(self, analyses: List[LLMAnalysisResult]) -> Dict[str, Dict]:
        """Calculate currency impact based on central bank analyses"""
        currency_impacts = {}
        
        for analysis in analyses:
            bank_config = self.bank_configs.get(analysis.bank)
            if not bank_config:
                continue
            
            currency = bank_config['currency']
            
            if currency not in currency_impacts:
                currency_impacts[currency] = {
                    'overall_bias': 'NEUTRAL',
                    'confidence': 0.0,
                    'market_impact': 'NEUTRAL',
                    'rate_outlook': 'RATE_HOLD',
                    'analyses': [],
                    'weighted_score': 0.0
                }
            
            # Add analysis
            currency_impacts[currency]['analyses'].append(analysis)
            
            # Calculate weighted score
            bias_scores = {'HAWKISH': 1.0, 'NEUTRAL': 0.0, 'DOVISH': -1.0}
            impact_scores = {'BULLISH': 1.0, 'NEUTRAL': 0.0, 'BEARISH': -1.0}
            
            bias_score = bias_scores.get(analysis.policy_bias, 0.0) * analysis.confidence
            impact_score = impact_scores.get(analysis.market_impact, 0.0) * analysis.confidence
            
            currency_impacts[currency]['weighted_score'] += bias_score
        
        # Calculate overall impact for each currency
        for currency, impact in currency_impacts.items():
            if impact['analyses']:
                avg_confidence = sum(a.confidence for a in impact['analyses']) / len(impact['analyses'])
                impact['confidence'] = avg_confidence
                
                # Determine overall bias
                if impact['weighted_score'] > 0.3:
                    impact['overall_bias'] = 'HAWKISH'
                    impact['market_impact'] = 'BULLISH'
                    impact['rate_outlook'] = 'RATE_UP'
                elif impact['weighted_score'] < -0.3:
                    impact['overall_bias'] = 'DOVISH'
                    impact['market_impact'] = 'BEARISH'
                    impact['rate_outlook'] = 'RATE_DOWN'
                else:
                    impact['overall_bias'] = 'NEUTRAL'
                    impact['market_impact'] = 'NEUTRAL'
                    impact['rate_outlook'] = 'RATE_HOLD'
        
        return currency_impacts
    
    def create_sample_statements(self) -> List[CentralBankStatement]:
        """Create sample central bank statements for testing"""
        now = datetime.now()
        
        samples = [
            CentralBankStatement(
                bank='FED',
                timestamp=now - timedelta(days=1),
                statement="The Federal Reserve remains committed to achieving maximum employment and inflation at 2 percent. While inflation has eased from its peak, it remains elevated. We will continue to monitor incoming data closely and adjust policy as appropriate. The economic outlook is uncertain and we remain prepared to respond to changing economic conditions.",
                source='FOMC Statement',
                statement_type='meeting',
                officials=['Jerome Powell']
            ),
            CentralBankStatement(
                bank='ECB',
                timestamp=now - timedelta(days=2),
                statement="Governing Council decided to keep the three key ECB interest rates unchanged. The incoming data suggest that inflation dynamics continue to weaken, reflecting the impact of our past rate increases and the transmission of monetary policy. We will continue to follow a data-dependent approach to determine the appropriate level and duration of restriction.",
                source='ECB Press Release',
                statement_type='press_release',
                officials=['Christine Lagarde']
            ),
            CentralBankStatement(
                bank='BOE',
                timestamp=now - timedelta(days=3),
                statement="The MPC voted by a majority of 6-3 to maintain Bank Rate at 5.25%. While inflation has fallen significantly, it remains above target. The economic outlook has improved modestly, but risks remain. We remain prepared to respond to any developments that could threaten the inflation target.",
                source='BOE Monetary Policy Summary',
                statement_type='meeting',
                officials=['Andrew Bailey']
            ),
            CentralBankStatement(
                bank='BOJ',
                timestamp=now - timedelta(days=4),
                statement="The Bank of Japan will continue with monetary easing until inflation is sustainably achieved at 2% accompanied by wage growth. While price developments have been positive, we need to carefully monitor whether wages and prices will continue to rise in a sustainable manner.",
                source='BOJ Statement',
                statement_type='press_release',
                officials=['Kazuo Ueda']
            )
        ]
        
        return samples

# Factory function
def create_llm_analyzer(api_key: Optional[str] = None) -> LLMCentralBankAnalyzer:
    """Create LLM central bank analyzer"""
    return LLMCentralBankAnalyzer(api_key=api_key)
