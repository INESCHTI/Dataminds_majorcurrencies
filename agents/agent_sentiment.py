"""
=====================================
MARKET SENTIMENT AGENT
FX-AlphaLab | Major Currencies
=====================================
ReAct Agent avec mémoire
LLM : FinBERT (local HuggingFace) pour le scoring NLP
      + Claude/TokenFactory/Ollama pour la synthèse narrative
Rôle : Analyse sentiment news + positioning marché
Output : signal (BUY/SELL/HOLD) + confidence + sentiment scores

Prerequisites:
  pip install transformers torch langchain>=0.2.0 langchain-ollama anthropic openai
  Models auto-downloaded from HuggingFace on first run:
    ProsusAI/finbert  (financial sentiment)
"""

import os
import json
import re
import sys
import warnings
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# HuggingFace FinBERT
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("[WARN] transformers not installed. pip install transformers torch")

# LLM providers
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
import MetaTrader5 as mt5

warnings.filterwarnings("ignore")


def load_environment_files() -> None:
    """Load agent and root .env files with encoding fallback for Windows."""
    current_file = Path(__file__).resolve()
    env_candidates = [
        current_file.parent / ".env",
        current_file.parents[1] / ".env",
    ]
    encodings = ("utf-8", "utf-8-sig", "utf-16")

    for env_path in env_candidates:
        if not env_path.exists():
            continue
        loaded = False
        for encoding in encodings:
            try:
                if load_dotenv(dotenv_path=env_path, override=False, encoding=encoding):
                    print(f"Loaded env: {env_path} (encoding={encoding})")
                loaded = True
                break
            except UnicodeDecodeError:
                continue
            except Exception as exc:
                print(f"Warning: failed to load {env_path} ({encoding}): {exc}")
                loaded = True
                break
        if not loaded:
            print(f"Warning: could not decode env file {env_path} with supported encodings")


load_environment_files()

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

LLM_PROVIDER = os.getenv("FX_LLM_PROVIDER", "local").strip().lower()

ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL     = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

TOKEN_FACTORY_MODEL    = os.getenv("TOKEN_FACTORY_MODEL", "hosted_vllm/Llama-3.1-70B-Instruct")
TOKEN_FACTORY_BASE_URL = os.getenv("TOKEN_FACTORY_BASE_URL", "https://tokenfactory.esprit.tn/api")
TOKEN_FACTORY_API_KEY  = os.getenv("TOKEN_FACTORY_API_KEY")

OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_FALLBACK_MODELS = [
    m.strip() for m in os.getenv("OLLAMA_FALLBACK_MODELS", "mistral,llama3.2,phi3").split(",") if m.strip()
]

# FinBERT model
FINBERT_MODEL   = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
FINBERT_DEVICE  = int(os.getenv("FINBERT_DEVICE", "-1"))  # -1=CPU, 0=GPU

PG_DSN = (
    f"host={os.getenv('POSTGRES_HOST')} "
    f"port={os.getenv('POSTGRES_PORT')} "
    f"dbname={os.getenv('POSTGRES_DB')} "
    f"user={os.getenv('POSTGRES_USER')} "
    f"password={os.getenv('POSTGRES_PASSWORD')}"
)

MT5_LOGIN    = os.getenv("MT5_LOGIN")
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER   = os.getenv("MT5_SERVER")

SMALL_ACCOUNT_MODE               = os.getenv("FX_SMALL_ACCOUNT_MODE","1").lower() in {"1","true","yes","on"}
SMALL_ACCOUNT_MAX_BALANCE        = float(os.getenv("FX_SMALL_ACCOUNT_MAX_BALANCE","150"))
SMALL_ACCOUNT_MIN_MARGIN_LEVEL   = float(os.getenv("FX_SMALL_ACCOUNT_MIN_MARGIN_LEVEL","200"))
SMALL_ACCOUNT_MIN_FREE_MARGIN    = float(os.getenv("FX_SMALL_ACCOUNT_MIN_FREE_MARGIN","20"))
SMALL_ACCOUNT_MAX_OPEN_POSITIONS = int(os.getenv("FX_SMALL_ACCOUNT_MAX_OPEN_POSITIONS","1"))
SMALL_ACCOUNT_CONFIDENCE_CAP     = float(os.getenv("FX_SMALL_ACCOUNT_CONFIDENCE_CAP","0.65"))

DEFAULT_PAIRS = [
    "EURUSD", "USDCHF", "GBPUSD", "USDJPY",
]
PAIRS_ENV = os.getenv("FX_PAIRS", "")
if PAIRS_ENV.strip():
    PAIRS = [p.strip().upper() for p in PAIRS_ENV.split(",") if p.strip()]
else:
    PAIRS = DEFAULT_PAIRS.copy()

# Remove duplicates while preserving order.
PAIRS = list(dict.fromkeys(PAIRS))
DEFAULT_SYMBOL = os.getenv("FX_DEFAULT_SYMBOL","EURUSD").upper()
RUN_ALL_SYMBOLS = os.getenv("FX_RUN_ALL_SYMBOLS","0").lower() in {"1","true","yes","on"}

PAIR_CURRENCIES = {
    "EURUSD": {"base":"EUR","quote":"USD"},
    "USDCHF": {"base":"USD","quote":"CHF"},
    "GBPUSD": {"base":"GBP","quote":"USD"},
    "USDJPY": {"base":"USD","quote":"JPY"},
}

# ─────────────────────────────────────────
# FINBERT SINGLETON
# ─────────────────────────────────────────

class FinBERTScorer:
    """
    Singleton FinBERT scorer.
    Chargé une seule fois, réutilisé pour tous les articles.
    Labels : positive → bullish | negative → bearish | neutral
    """
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.available = False
        self.pipe      = None
        if not TRANSFORMERS_AVAILABLE:
            print("   [WARN] FinBERT unavailable — using lexical fallback")
            return
        try:
            print(f"   Loading FinBERT ({FINBERT_MODEL})...")
            self.pipe = pipeline(
                "text-classification",
                model=FINBERT_MODEL,
                tokenizer=FINBERT_MODEL,
                device=FINBERT_DEVICE,
                top_k=None,          # retourne tous les labels
                truncation=True,
                max_length=512,
            )
            self.available = True
            print("   [OK] FinBERT loaded")
        except Exception as e:
            print(f"   [WARN] FinBERT load failed: {e} — using lexical fallback")

    def score(self, text: str) -> dict:
        """
        Score un texte.
        Returns: {"score": float [-1,+1], "label": str, "positive": p, "negative": n, "neutral": u}
        """
        if not text or not text.strip():
            return {"score": 0.0, "label": "neutral", "positive": 0.0, "negative": 0.0, "neutral": 1.0}

        if self.available and self.pipe:
            try:
                # Tronquer à 512 tokens max
                text_trunc = text[:1000]
                results    = self.pipe(text_trunc)[0]
                scores     = {r["label"].lower(): r["score"] for r in results}
                pos = scores.get("positive", 0.0)
                neg = scores.get("negative", 0.0)
                neu = scores.get("neutral",  0.0)
                # Score normalisé : +1 = très bullish, -1 = très bearish
                sentiment_score = round(pos - neg, 4)
                label = "positive" if pos > neg and pos > neu else \
                        "negative" if neg > pos and neg > neu else "neutral"
                return {"score": sentiment_score, "label": label,
                        "positive": round(pos,4), "negative": round(neg,4), "neutral": round(neu,4)}
            except Exception as e:
                print(f"   [WARN] FinBERT inference error: {e}")

        # Fallback lexical
        return self._lexical_score(text)

    def score_batch(self, texts: list) -> list:
        """Score une liste de textes."""
        return [self.score(t) for t in texts]

    @staticmethod
    def _lexical_score(text: str) -> dict:
        """Score basique par dictionnaire si FinBERT indisponible."""
        BULL = ["rise","rally","gain","bullish","surge","strong","positive","growth",
                "recovery","boost","higher","beat","exceed","hawkish","optimism"]
        BEAR = ["fall","drop","decline","bearish","weak","negative","loss","recession",
                "crash","lower","miss","disappoint","fear","dovish","concern","risk"]
        t    = text.lower()
        b    = sum(1 for w in BULL if w in t)
        br   = sum(1 for w in BEAR if w in t)
        tot  = b + br
        if tot == 0:
            return {"score":0.0,"label":"neutral","positive":0.0,"negative":0.0,"neutral":1.0}
        s = round((b - br) / tot, 4)
        return {"score":s, "label":"positive" if s>0.1 else "negative" if s<-0.1 else "neutral",
                "positive":round(b/tot,4),"negative":round(br/tot,4),"neutral":0.0}


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def pg_connect():
    return psycopg2.connect(PG_DSN)


def load_news(symbol: str, days: int = 7) -> pd.DataFrame:
    """Charge les news liées à une paire depuis PostgreSQL."""
    currencies = PAIR_CURRENCIES.get(symbol, {})
    base  = currencies.get("base","")
    quote = currencies.get("quote","")
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        conn = pg_connect()
        df   = pd.read_sql(
            f"""
            SELECT article_id, title, content, source, published_at, currencies
            FROM news_articles
            WHERE published_at >= '{since}'
            AND (currencies @> ARRAY['{base}']::varchar[]
                 OR currencies @> ARRAY['{quote}']::varchar[]
                 OR currencies @> ARRAY['USD']::varchar[])
            ORDER BY published_at DESC
            LIMIT 100
            """,
            conn
        )
        conn.close()
        df["published_at"] = pd.to_datetime(df["published_at"])
        return df
    except Exception as e:
        print(f"   [WARN] News load error: {e}")
        return pd.DataFrame()


def get_mt5_account_snapshot() -> dict:
    if not MT5_LOGIN or not MT5_PASSWORD or not MT5_SERVER:
        return {"available": False, "reason": "MT5 credentials not configured"}
    connected = False
    try:
        connected = mt5.initialize()
        if not connected:
            return {"available": False, "reason": f"MT5 init failed: {mt5.last_error()}"}
        if not mt5.login(int(MT5_LOGIN), MT5_PASSWORD, MT5_SERVER):
            return {"available": False, "reason": f"MT5 login failed: {mt5.last_error()}"}
        account   = mt5.account_info()
        positions = mt5.positions_get() or []
        exposure  = {}
        for pos in positions:
            sym = getattr(pos, "symbol","UNKNOWN")
            exposure[sym] = exposure.get(sym,0) + float(getattr(pos,"volume",0) or 0)
        return {
            "available":True,
            "balance":       float(getattr(account,"balance",0) or 0),
            "equity":        float(getattr(account,"equity",0) or 0),
            "free_margin":   float(getattr(account,"margin_free",0) or 0),
            "margin_level":  float(getattr(account,"margin_level",0) or 0),
            "leverage":      int(getattr(account,"leverage",0) or 0),
            "positions_count": len(positions),
            "symbol_exposure": exposure,
        }
    except Exception as e:
        return {"available":False,"reason":str(e)}
    finally:
        if connected:
            mt5.shutdown()


def apply_small_account_risk_guard(signal_data: dict, account_snapshot: dict) -> dict:
    if not SMALL_ACCOUNT_MODE:
        signal_data["risk_mode"] = "disabled"; return signal_data
    if not account_snapshot.get("available"):
        signal_data["risk_mode"] = "small_account_no_snapshot"; return signal_data
    balance = float(account_snapshot.get("balance",0) or 0)
    if balance > SMALL_ACCOUNT_MAX_BALANCE:
        signal_data["risk_mode"] = "standard"; return signal_data

    signal     = str(signal_data.get("signal","HOLD")).upper()
    confidence = float(signal_data.get("confidence",0.5) or 0.5)
    free_margin    = float(account_snapshot.get("free_margin",0) or 0)
    margin_level   = float(account_snapshot.get("margin_level",0) or 0)
    positions_count = int(account_snapshot.get("positions_count",0) or 0)
    reasons = []

    if confidence > SMALL_ACCOUNT_CONFIDENCE_CAP:
        confidence = SMALL_ACCOUNT_CONFIDENCE_CAP
        reasons.append("confidence capped")
    if positions_count >= SMALL_ACCOUNT_MAX_OPEN_POSITIONS and signal in {"BUY","SELL"}:
        signal = "HOLD"; confidence = min(confidence,0.45)
        reasons.append("max positions reached")
    if free_margin < SMALL_ACCOUNT_MIN_FREE_MARGIN and signal in {"BUY","SELL"}:
        signal = "HOLD"; confidence = min(confidence,0.40)
        reasons.append("free margin low")
    if margin_level > 0 and margin_level < SMALL_ACCOUNT_MIN_MARGIN_LEVEL and signal in {"BUY","SELL"}:
        signal = "HOLD"; confidence = min(confidence,0.40)
        reasons.append("margin level low")

    signal_data.update({
        "signal": signal, "confidence": round(confidence,2),
        "risk_mode": "small_account_100",
        "risk_constraints": {
            "max_balance": SMALL_ACCOUNT_MAX_BALANCE,
            "min_margin_level": SMALL_ACCOUNT_MIN_MARGIN_LEVEL,
            "min_free_margin": SMALL_ACCOUNT_MIN_FREE_MARGIN,
            "max_open_positions": SMALL_ACCOUNT_MAX_OPEN_POSITIONS,
            "confidence_cap": SMALL_ACCOUNT_CONFIDENCE_CAP,
        }
    })
    if reasons:
        signal_data["risk_adjustments"] = reasons
    return signal_data


# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────

@tool
def score_news_sentiment(symbol: str) -> str:
    """
    Score sentiment of recent news articles for a forex pair using FinBERT.
    Returns per-article scores + aggregated sentiment metrics.
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        df     = load_news(symbol, days=7)
        if df.empty:
            return json.dumps({"symbol":symbol,"articles_found":0,
                               "message":"No recent news","overall_score":0.0})

        scorer  = FinBERTScorer.get()
        results = []

        for _, row in df.iterrows():
            text  = f"{row['title']} {row.get('content','')}"[:800]
            score = scorer.score(text)
            results.append({
                "title":        row["title"][:100],
                "source":       row["source"],
                "date":         str(row["published_at"])[:16],
                "sentiment":    score["label"],
                "score":        score["score"],
                "positive":     score["positive"],
                "negative":     score["negative"],
                "neutral":      score["neutral"],
            })

        scores = [r["score"] for r in results]
        pos_count = sum(1 for r in results if r["sentiment"] == "positive")
        neg_count = sum(1 for r in results if r["sentiment"] == "negative")
        neu_count = sum(1 for r in results if r["sentiment"] == "neutral")

        overall = round(float(np.mean(scores)), 4) if scores else 0.0
        rolling_3h = [r for r in results
                      if (datetime.now() - pd.to_datetime(r["date"])).total_seconds() < 10800]
        rolling_3h_score = round(float(np.mean([r["score"] for r in rolling_3h])), 4) \
                           if rolling_3h else 0.0

        return json.dumps({
            "symbol":           symbol,
            "articles_analyzed": len(results),
            "overall_score":    overall,          # -1 bearish → +1 bullish
            "rolling_3h_score": rolling_3h_score,
            "distribution": {
                "positive": pos_count,
                "negative": neg_count,
                "neutral":  neu_count,
            },
            "bullish_ratio":    round(pos_count / len(results), 3) if results else 0,
            "bearish_ratio":    round(neg_count / len(results), 3) if results else 0,
            "sentiment_label":  "BULLISH" if overall > 0.1 else "BEARISH" if overall < -0.1 else "NEUTRAL",
            "momentum":         round(rolling_3h_score - overall, 4),  # positif = sentiment qui s'améliore
            "top_articles":     results[:5],
            "finbert_used":     FinBERTScorer.get().available,
        }, indent=2, default=str)

    except Exception as e:
        return f"Error: {e}"


@tool
def get_sentiment_trend(symbol: str) -> str:
    """
    Analyze sentiment trend over time (24H vs 72H vs 7D) to detect shifts.
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        scorer = FinBERTScorer.get()
        windows = {"24h": 1, "72h": 3, "7d": 7}
        trend   = {}

        for label, days in windows.items():
            df = load_news(symbol, days=days)
            if df.empty:
                trend[label] = {"score": 0.0, "count": 0, "label": "NEUTRAL"}
                continue
            texts  = [f"{r['title']} {r.get('content','')}"[:600]
                      for _, r in df.iterrows()]
            scores = [scorer.score(t)["score"] for t in texts]
            avg    = round(float(np.mean(scores)), 4) if scores else 0.0
            trend[label] = {
                "score": avg,
                "count": len(scores),
                "label": "BULLISH" if avg > 0.1 else "BEARISH" if avg < -0.1 else "NEUTRAL",
            }

        # Momentum : est-ce que le sentiment s'améliore ou se dégrade ?
        s24 = trend["24h"]["score"]
        s7d = trend["7d"]["score"]
        momentum = round(s24 - s7d, 4)
        trend["momentum"] = {
            "value":  momentum,
            "signal": "IMPROVING" if momentum > 0.05 else "DETERIORATING" if momentum < -0.05 else "STABLE",
        }

        return json.dumps({"symbol": symbol, "trend": trend}, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool
def detect_high_impact_news(symbol: str) -> str:
    """
    Detect breaking or high-impact news that could cause sudden price moves.
    Flags: central bank statements, NFP, CPI releases, geopolitical events.
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        df     = load_news(symbol, days=2)
        if df.empty:
            return json.dumps({"symbol":symbol,"high_impact_detected":False,"events":[]})

        HIGH_IMPACT_KEYWORDS = [
            "federal reserve","fed","ecb","boj","boe","snb",
            "interest rate","rate decision","rate hike","rate cut",
            "nonfarm payroll","nfp","cpi","inflation","gdp",
            "unemployment","hawkish","dovish","quantitative",
            "emergency","crisis","war","sanction","geopolit",
            "intervention","default","recession","bailout"
        ]

        scorer  = FinBERTScorer.get()
        events  = []

        for _, row in df.iterrows():
            title   = str(row["title"]).lower()
            content = str(row.get("content","")).lower()
            text    = f"{title} {content}"

            impact_score = sum(1 for kw in HIGH_IMPACT_KEYWORDS if kw in text)
            if impact_score >= 2:
                sent = scorer.score(f"{row['title']} {row.get('content','')}"[:600])
                events.append({
                    "title":        row["title"][:120],
                    "source":       row["source"],
                    "date":         str(row["published_at"])[:16],
                    "impact_score": impact_score,
                    "sentiment":    sent["label"],
                    "score":        sent["score"],
                    "keywords_hit": [kw for kw in HIGH_IMPACT_KEYWORDS if kw in text][:5],
                })

        events.sort(key=lambda x: x["impact_score"], reverse=True)

        return json.dumps({
            "symbol":               symbol,
            "high_impact_detected": len(events) > 0,
            "event_count":          len(events),
            "max_impact_score":     events[0]["impact_score"] if events else 0,
            "dominant_sentiment":   events[0]["sentiment"] if events else "neutral",
            "events":               events[:5],
            "recommendation":       "REDUCE_CONFIDENCE" if len(events) >= 3 else "NORMAL",
        }, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_source_credibility_weighted_score(symbol: str) -> str:
    """
    Compute sentiment score weighted by source credibility.
    Premium sources (Reuters, Bloomberg) get higher weight than blogs.
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        df     = load_news(symbol, days=5)
        if df.empty:
            return json.dumps({"symbol":symbol,"weighted_score":0.0,"message":"No news"})

        SOURCE_WEIGHTS = {
            "reuters":      1.0,
            "bloomberg":    1.0,
            "ft":           0.9,
            "wsj":          0.9,
            "forexlive":    0.8,
            "fxstreet":     0.75,
            "dailyfx":      0.7,
            "investing.com":0.65,
        }
        DEFAULT_WEIGHT = 0.5

        scorer   = FinBERTScorer.get()
        weighted = []
        total_w  = 0.0

        for _, row in df.iterrows():
            src    = str(row["source"]).lower()
            weight = next((v for k,v in SOURCE_WEIGHTS.items() if k in src), DEFAULT_WEIGHT)
            text   = f"{row['title']} {row.get('content','')}"[:600]
            score  = scorer.score(text)["score"]
            weighted.append(score * weight)
            total_w += weight

        w_score = round(sum(weighted) / total_w, 4) if total_w > 0 else 0.0

        return json.dumps({
            "symbol":              symbol,
            "weighted_score":      w_score,
            "articles_used":       len(weighted),
            "sentiment_label":     "BULLISH" if w_score > 0.1 else "BEARISH" if w_score < -0.1 else "NEUTRAL",
            "source_breakdown":    {
                "premium_sources": sum(1 for _,r in df.iterrows()
                                       if any(k in str(r["source"]).lower()
                                              for k in ["reuters","bloomberg","ft","wsj"])),
                "total_sources":   len(df),
            }
        }, indent=2)
    except Exception as e:
        return f"Error: {e}"


# ─────────────────────────────────────────
# TOOLS LIST
# ─────────────────────────────────────────

TOOLS = [
    score_news_sentiment,
    get_sentiment_trend,
    detect_high_impact_news,
    get_source_credibility_weighted_score,
]

# ─────────────────────────────────────────
# SENTIMENT AGENT CLASS
# ─────────────────────────────────────────

class MarketSentimentAgent:
    """
    ReAct Agent pour l'analyse de sentiment.
    FinBERT (local) pour le scoring NLP.
    LLM pour la synthèse narrative.
    Mémoire : historique des 20 derniers messages.
    """

    def __init__(self):
        print("Initializing Market Sentiment Agent...")

        # Charger FinBERT une seule fois
        self.scorer = FinBERTScorer.get()

        self.provider  = LLM_PROVIDER
        self.llm_model = None
        self.llm       = None
        self.claude_client = None
        self.tf_client     = None

        if self.provider == "claude":
            if anthropic is None:
                raise RuntimeError("pip install anthropic")
            if not ANTHROPIC_API_KEY:
                raise RuntimeError("ANTHROPIC_API_KEY missing")
            self.claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.llm_model     = ANTHROPIC_MODEL

        elif self.provider == "tokenfactory":
            if OpenAI is None:
                raise RuntimeError("pip install openai")
            if not TOKEN_FACTORY_API_KEY:
                raise RuntimeError("TOKEN_FACTORY_API_KEY missing")
            self.tf_client = OpenAI(
                api_key=TOKEN_FACTORY_API_KEY,
                base_url=TOKEN_FACTORY_BASE_URL,
            )
            self.llm_model = TOKEN_FACTORY_MODEL

        else:
            self.llm = ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=0.1,
                num_predict=2048,
            )
            self.llm_model = OLLAMA_MODEL

        self.chat_history   = []
        self.signal_history = []

        print(f"   LLM     : {self.llm_model} ({self.provider})")
        print(f"   NLP     : {'FinBERT (ProsusAI)' if self.scorer.available else 'Lexical fallback'}")
        print(f"   Tools   : {[t.name for t in TOOLS]}")
        print("   [OK] Ready!\n")

    def _invoke_llm(self, messages: list, system: str = "") -> str:
        if self.provider == "claude":
            payload = [{"role": "user" if isinstance(m,HumanMessage) else "assistant",
                        "content": m.content} for m in messages]
            resp = self.claude_client.messages.create(
                model=self.llm_model, max_tokens=2048,
                system=system or "You are an expert market sentiment analyst for Forex.",
                messages=payload,
            )
            return resp.content[0].text

        if self.provider == "tokenfactory":
            payload = []
            if system:
                payload.append({"role":"system","content":system})
            for m in messages:
                payload.append({"role":"user" if isinstance(m,HumanMessage) else "assistant",
                                 "content":m.content})
            resp = self.tf_client.chat.completions.create(
                model=TOKEN_FACTORY_MODEL, messages=payload,
                temperature=0.1, max_tokens=2048,
            )
            return resp.choices[0].message.content

        # Ollama + fallback
        tried = [OLLAMA_MODEL]
        try:
            return self.llm.invoke(messages).content
        except Exception as e:
            if "not found" not in str(e).lower() and "404" not in str(e):
                raise
            for m in OLLAMA_FALLBACK_MODELS:
                if m == OLLAMA_MODEL: continue
                tried.append(m)
                try:
                    print(f"   [WARN] Fallback: {m}")
                    fb = ChatOllama(model=m, base_url=OLLAMA_BASE_URL, temperature=0.1)
                    result = fb.invoke(messages).content
                    self.llm = fb
                    print(f"   [OK] Active: {m}")
                    return result
                except Exception:
                    continue
            raise RuntimeError(f"No Ollama model. Tried: {', '.join(tried)}")

    def analyze(self, symbol: str) -> dict:
        print(f"\n{'='*55}\n  SENTIMENT ANALYSIS — {symbol}\n{'='*55}")

        # ── STEP 1 : Collecte des vraies données sentiment
        print("   Scoring news with FinBERT...")
        sent_scores   = score_news_sentiment.invoke(symbol)
        sent_trend    = get_sentiment_trend.invoke(symbol)
        high_impact   = detect_high_impact_news.invoke(symbol)
        weighted_sent = get_source_credibility_weighted_score.invoke(symbol)
        account_snap  = get_mt5_account_snapshot()
        print("   [OK] Sentiment data collected")

        # ── STEP 2 : LLM synthèse sentiment
        system_prompt = (
            "You are a market sentiment analyst specializing in Forex. "
            "You interpret NLP sentiment scores from financial news to assess "
            "market psychology and generate directional trading signals. "
            "Always base your analysis strictly on the provided data."
        )

        synthesis_prompt = f"""
Analyze market sentiment for {symbol} and generate a trading signal.

RAW SENTIMENT SCORES (FinBERT NLP):
{sent_scores}

SENTIMENT TREND (24H vs 72H vs 7D):
{sent_trend}

HIGH-IMPACT NEWS DETECTION:
{high_impact}

CREDIBILITY-WEIGHTED SENTIMENT:
{weighted_sent}

MT5 ACCOUNT SNAPSHOT:
{json.dumps(account_snap, indent=2)}

ANALYSIS FRAMEWORK:
1. Overall sentiment direction (bullish/bearish/neutral)
2. Sentiment momentum (improving or deteriorating)
3. High-impact news risk (reduce confidence if present)
4. Credibility-weighted confirmation
5. If small account or high event risk → conservative signal

Provide:
1. Sentiment narrative (3-4 sentences)
2. Key news themes driving sentiment
3. Final JSON signal:

```json
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0-1.0,
  "reasoning": "sentiment-based explanation",
  "sentiment_score": -1.0 to 1.0,
  "sentiment_label": "BULLISH" | "BEARISH" | "NEUTRAL",
  "sentiment_momentum": "IMPROVING" | "DETERIORATING" | "STABLE",
  "high_impact_risk": true | false,
  "news_volume": number
}}
```
Be conservative if high_impact_risk is true. Only use BUY, SELL, or HOLD.
"""

        try:
            self.chat_history.append(HumanMessage(content=synthesis_prompt))
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]

            output = self._invoke_llm(self.chat_history, system=system_prompt)
            self.chat_history.append(AIMessage(content=output))

            print(f"\nLLM Sentiment Synthesis:\n{output[:600]}...")

            signal_data = self._parse_signal(output, symbol)
            signal_data = apply_small_account_risk_guard(signal_data, account_snap)
            signal_data.update({
                "timestamp": datetime.utcnow().isoformat(),
                "agent":     "sentiment",
                "nlp_model": "finbert" if self.scorer.available else "lexical",
                "raw_data":  {
                    "sentiment_scores":  sent_scores,
                    "sentiment_trend":   sent_trend,
                    "high_impact_news":  high_impact,
                    "weighted_sentiment":weighted_sent,
                    "account_snapshot":  account_snap,
                }
            })
            self.signal_history.append(signal_data)
            self._save_signal(signal_data, symbol)
            return signal_data

        except Exception as e:
            print(f"   [ERROR] LLM error: {e}")
            return self._fallback_signal(symbol)

    def _parse_signal(self, output: str, symbol: str) -> dict:
        try:
            m = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
            if m:
                d = json.loads(m.group(1)); d["symbol"] = symbol; return d
            m = re.search(r'\{[^{}]*"signal"[^{}]*\}', output, re.DOTALL)
            if m:
                d = json.loads(m.group(0)); d["symbol"] = symbol; return d
        except Exception:
            pass
        sig = "HOLD"
        if "BUY"  in output.upper(): sig = "BUY"
        elif "SELL" in output.upper(): sig = "SELL"
        return {"symbol":symbol,"signal":sig,"confidence":0.5,"reasoning":output[:400]}

    def _fallback_signal(self, symbol: str) -> dict:
        """Fallback basé sur FinBERT directement sans LLM."""
        print("   [WARN] Fallback: FinBERT direct scoring")
        try:
            df = load_news(symbol, days=3)
            if df.empty:
                return {"symbol":symbol,"signal":"HOLD","confidence":0.0}

            scorer = FinBERTScorer.get()
            scores = [scorer.score(f"{r['title']} {r.get('content','')}"[:600])["score"]
                      for _, r in df.iterrows()]
            avg = float(np.mean(scores)) if scores else 0.0

            if avg > 0.15:   signal, conf = "BUY",  round(0.5 + avg * 0.3, 2)
            elif avg < -0.15: signal, conf = "SELL", round(0.5 + abs(avg) * 0.3, 2)
            else:             signal, conf = "HOLD", 0.40

            conf = min(conf, 0.70)
            fb = {
                "symbol":symbol,"signal":signal,"confidence":conf,
                "reasoning":f"FinBERT avg={avg:.3f} over {len(scores)} articles",
                "sentiment_score":round(avg,4),
                "sentiment_label":"BULLISH" if avg>0.1 else "BEARISH" if avg<-0.1 else "NEUTRAL",
            }
            return apply_small_account_risk_guard(fb, get_mt5_account_snapshot())
        except Exception as e:
            return {"symbol":symbol,"signal":"HOLD","confidence":0.0,"reasoning":str(e)}

    def _save_signal(self, signal: dict, symbol: str):
        os.makedirs("outputs/signals", exist_ok=True)
        path = f"outputs/signals/sentiment_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        with open(path, "w") as f:
            json.dump(signal, f, indent=2, default=str)
        print(f"\n   Saved signal -> {path}")


# ─────────────────────────────────────────
# CLI HELPERS
# ─────────────────────────────────────────

def resolve_target_symbol() -> str:
    if len(sys.argv) > 1:
        c = sys.argv[1].upper().strip()
    else:
        c = DEFAULT_SYMBOL
    if c not in PAIRS:
        raise ValueError(f"Invalid symbol '{c}'. Allowed: {', '.join(PAIRS)}")
    return c

def should_run_all_symbols() -> bool:
    if RUN_ALL_SYMBOLS: return True
    if len(sys.argv) <= 1: return True
    return sys.argv[1].upper().strip() == "ALL"

def print_comparison_report(signals: list) -> None:
    if not signals: return
    ranked = sorted(signals, key=lambda x: (
        {"BUY":0,"SELL":1,"HOLD":2}.get(str(x.get("signal","HOLD")).upper(),3),
        -float(x.get("confidence",0) or 0)
    ))
    print(f"\n{'='*72}\n  SENTIMENT MULTI-PAIR REPORT\n{'='*72}")
    for item in ranked:
        sym   = item.get("symbol","?")
        sig   = item.get("signal","HOLD")
        conf  = float(item.get("confidence",0) or 0)
        slabel = item.get("sentiment_label","N/A")
        mom   = item.get("sentiment_momentum","N/A")
        hip   = item.get("high_impact_risk", False)
        print(f"  {sym:<6} -> {sig:<4} ({conf:.0%}) | sentiment={slabel} | momentum={mom} | high_impact={hip}")
    best = ranked[0]
    print(f"\n  Best: {best.get('symbol','?')} -> {best.get('signal','HOLD')} ({float(best.get('confidence',0) or 0):.0%})")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("="*55)
    print("  MARKET SENTIMENT AGENT")
    print("  FX-AlphaLab | Major Currencies")
    print("="*55)
    print(f"\n  Provider : {LLM_PROVIDER}")
    print(f"  NLP Model: {FINBERT_MODEL}\n")

    agent = MarketSentimentAgent()

    if should_run_all_symbols():
        print(f"   Mode: ALL pairs ({', '.join(PAIRS)})")
        signals = [agent.analyze(sym) for sym in PAIRS]
        print_comparison_report(signals)
    else:
        symbol = resolve_target_symbol()
        print(f"   Target: {symbol}")
        signal = agent.analyze(symbol)
        conf   = float(signal.get("confidence",0) or 0)
        print(f"\n{'='*55}")
        print(f"  RESULT    : {signal.get('signal')}  ({conf:.0%})")
        print(f"  Sentiment : {signal.get('sentiment_label','N/A')} ({signal.get('sentiment_score',0)})")
        print(f"  Momentum  : {signal.get('sentiment_momentum','N/A')}")
        print(f"  High Risk : {signal.get('high_impact_risk',False)}")
        print(f"  Reason    : {str(signal.get('reasoning',''))[:200]}")
        print(f"{'='*55}")