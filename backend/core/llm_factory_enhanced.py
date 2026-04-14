"""
Enhanced Local LLM Factory - Stable Transformers Integration
Avoids DLL issues while providing NLP capabilities
"""
import os
import warnings
from typing import Dict, List, Optional

# Disable transformers warnings
warnings.filterwarnings("ignore", category=UserWarning)

try:
    # Try CPU-only transformers to avoid GPU/DLL issues
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    
    # Force CPU mode to avoid GPU/DLL issues
    torch.set_grad_enabled(False)
    torch.device("cpu")  # Force CPU mode
    
    LOCAL_MODELS_AVAILABLE = True
    print("CPU-only Transformers available")
except Exception as e:
    print(f"Transformers not available: {e}")
    LOCAL_MODELS_AVAILABLE = False


class EnhancedLocalLLMFactory:
    """
    Enhanced local LLM with stable transformers integration
    """
    
    def __init__(self):
        self.device = "cpu"  # Force CPU
        self.models = {}
        
        if LOCAL_MODELS_AVAILABLE:
            self._load_lightweight_models()
    
    def _load_lightweight_models(self):
        """Load lightweight CPU models"""
        try:
            # Use very small models to avoid memory issues
            model_configs = {
                'sentiment': {
                    'model': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                    'max_length': 128
                },
                'classification': {
                    'model': 'distilbert-base-uncased-finetuned-sst-2-english', 
                    'max_length': 64
                }
            }
            
            for task, config in model_configs.items():
                try:
                    print(f"Loading {task} model...")
                    tokenizer = AutoTokenizer.from_pretrained(config['model'])
                    model = AutoModelForSequenceClassification.from_pretrained(
                        config['model'],
                        torch_dtype=torch.float32  # Force float32
                    )
                    
                    self.models[task] = {
                        'tokenizer': tokenizer,
                        'model': model,
                        'max_length': config['max_length']
                    }
                    print(f"Successfully loaded {task} model")
                    
                except Exception as e:
                    print(f"Failed to load {task} model: {e}")
                    continue
                    
        except Exception as e:
            print(f"Model loading failed: {e}")
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Enhanced sentiment analysis"""
        if not LOCAL_MODELS_AVAILABLE or 'sentiment' not in self.models:
            return self._rule_based_sentiment(text)
        
        try:
            model_config = self.models['sentiment']
            tokenizer = model_config['tokenizer']
            model = model_config['model']
            
            # Tokenize with truncation
            inputs = tokenizer(
                text[:model_config['max_length']], 
                truncation=True, 
                padding=True, 
                return_tensors="pt"
            )
            
            # Get prediction
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = outputs.logits.softmax(dim=-1)
                
            # Get best prediction
            scores = predictions[0].tolist()
            labels = ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
            best_idx = scores.index(max(scores))
            
            return {
                'label': labels[best_idx],
                'score': max(scores),
                'source': 'local_model_enhanced',
                'model': 'twitter-roberta-base-sentiment'
            }
            
        except Exception as e:
            print(f"Model error: {e}")
            return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> Dict:
        """Fallback rule-based sentiment"""
        # ... existing rule-based logic
        return {
            'label': 'NEUTRAL',
            'score': 0.5,
            'source': 'rule_based_fallback'
        }
    
    def extract_currencies(self, text: str) -> List[str]:
        """
        Extract currency codes from text
        Returns list of detected currency codes
        """
        # Common forex currency codes
        currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RON'
        ]
        
        found_currencies = []
        text_upper = text.upper()
        
        for currency in currencies:
            if currency in text_upper:
                found_currencies.append(currency)
        
        return list(set(found_currencies))  # Remove duplicates


# Global instance
_enhanced_llm_factory = None

def get_enhanced_llm_factory() -> EnhancedLocalLLMFactory:
    """Get singleton instance"""
    global _enhanced_llm_factory
    if _enhanced_llm_factory is None:
        _enhanced_llm_factory = EnhancedLocalLLMFactory()
    return _enhanced_llm_factory
