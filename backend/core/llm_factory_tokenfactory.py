"""
Enhanced LLM Factory using TokenFactory API with Llama models
"""

import os
import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenFactoryLLM:
    """TokenFactory API client for Llama models"""
    
    def __init__(self):
        self.api_key = os.getenv('TOKENFACTORY_API_KEY')
        self.base_url = os.getenv('TOKENFACTORY_BASE_URL', 'https://tokenfactory.esprit.tn/api')
        self.model = os.getenv('TOKENFACTORY_MODEL', 'hosted_vllm/Llama-3.1-70B-Instruct')
        
        if not self.api_key or self.api_key == 'YOUR_API_KEY':
            logger.warning("TokenFactory API key not configured, using fallback")
            self.enabled = False
        else:
            self.enabled = True
    
    def create_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """
        Create a chat completion using TokenFactory API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Response dictionary mimicking OpenAI format
        """
        if not self.enabled:
            return self._fallback_response(messages)
        
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 500),
                "top_p": kwargs.get('top_p', 0.9),
                "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
                "presence_penalty": kwargs.get('presence_penalty', 0.0)
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"TokenFactory API success: {len(result.get('choices', []))} choices")
                return result
            else:
                logger.error(f"TokenFactory API error: {response.status_code} - {response.text}")
                return self._fallback_response(messages)
                
        except Exception as e:
            logger.error(f"TokenFactory API request failed: {e}")
            return self._fallback_response(messages)
    
    def _fallback_response(self, messages: List[Dict]) -> Dict:
        """Fallback response when API is unavailable"""
        user_message = messages[-1].get('content', '') if messages else ''
        
        # Simple rule-based fallback
        if 'buy' in user_message.lower() or 'achat' in user_message.lower():
            content = "Based on current market conditions, a BUY signal may be considered with proper risk management."
        elif 'sell' in user_message.lower() or 'vente' in user_message.lower():
            content = "Based on current market conditions, a SELL signal may be considered with proper risk management."
        else:
            content = "Market analysis suggests careful monitoring of current conditions before making trading decisions."
        
        return {
            "choices": [{
                "message": {
                    "content": content,
                    "role": "assistant"
                }
            }]
        }

# Global instance
tokenfactory_llm = TokenFactoryLLM()

def get_tokenfactory_llm() -> TokenFactoryLLM:
    """Get the TokenFactory LLM instance"""
    return tokenfactory_llm

class EnhancedAgentReasoning:
    """Enhanced reasoning for FX agents using TokenFactory LLM"""
    
    def __init__(self):
        self.llm = get_tokenfactory_llm()
    
    def analyze_market_signal(self, agent_type: str, market_data: Dict, 
                            additional_context: str = "") -> Dict:
        """
        Generate sophisticated market signal analysis using LLM
        
        Args:
            agent_type: Type of agent (technical, macro, sentiment, geopolitical)
            market_data: Market data dictionary
            additional_context: Additional context for analysis
            
        Returns:
            Analysis result with signal, confidence, and reasoning
        """
        # Build context-specific prompt
        system_prompt = self._build_system_prompt(agent_type)
        user_prompt = self._build_user_prompt(agent_type, market_data, additional_context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get LLM response
        response = self.llm.create_completion(
            messages,
            temperature=0.3,  # Lower temperature for consistent trading signals
            max_tokens=300,
            top_p=0.8
        )
        
        # Parse response
        content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        return self._parse_analysis_response(content, agent_type)
    
    def _build_system_prompt(self, agent_type: str) -> str:
        """Build system prompt based on agent type"""
        base_prompt = """You are an expert FX trading analyst specializing in {agent_type} analysis.
        
Your task is to analyze market data and provide:
1. A clear trading signal (BUY/SELL/NEUTRAL)
2. A confidence level (0-100%)
3. Detailed reasoning for your decision

Format your response as:
SIGNAL: [BUY/SELL/NEUTRAL]
CONFIDENCE: [0-100]%
REASONING: [Your detailed analysis]

Be concise but thorough. Focus on risk management and probability-based decision making."""
        
        return base_prompt.format(agent_type=agent_type)
    
    def _build_user_prompt(self, agent_type: str, market_data: Dict, 
                          additional_context: str) -> str:
        """Build user prompt with market data"""
        prompt = f"""Analyze the following {agent_type} data for FX trading:

Current Market Data:
{json.dumps(market_data, indent=2)}

"""
        
        if additional_context:
            prompt += f"Additional Context:\n{additional_context}\n\n"
        
        prompt += "Provide your trading signal analysis based on this data."
        
        return prompt
    
    def _parse_analysis_response(self, content: str, agent_type: str) -> Dict:
        """Parse LLM response into structured format"""
        signal = "NEUTRAL"
        confidence = 50
        reasoning = content
        
        # Extract signal
        for line in content.split('\n'):
            if 'SIGNAL:' in line.upper():
                signal_part = line.split('SIGNAL:')[-1].strip().upper()
                if 'BUY' in signal_part:
                    signal = "BUY"
                elif 'SELL' in signal_part:
                    signal = "SELL"
                else:
                    signal = "NEUTRAL"
                break
        
        # Extract confidence
        for line in content.split('\n'):
            if 'CONFIDENCE:' in line.upper():
                try:
                    confidence_part = line.split('CONFIDENCE:')[-1].strip()
                    confidence = int(''.join(filter(str.isdigit, confidence_part)))
                    confidence = max(0, min(100, confidence))  # Clamp to 0-100
                except:
                    confidence = 50
                break
        
        # Extract reasoning
        for line in content.split('\n'):
            if 'REASONING:' in line.upper():
                reasoning = line.split('REASONING:')[-1].strip()
                break
        
        return {
            'signal': signal,
            'confidence': confidence / 100.0,  # Convert to 0-1 range
            'reasoning': reasoning,
            'agent_type': agent_type,
            'timestamp': datetime.now().isoformat()
        }

# Global enhanced reasoning instance
enhanced_reasoning = EnhancedAgentReasoning()

def get_enhanced_reasoning() -> EnhancedAgentReasoning:
    """Get the enhanced reasoning instance"""
    return enhanced_reasoning
