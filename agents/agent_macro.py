"""
=====================================
MACROECONOMIC EVENT AGENT
FX-AlphaLab | Major Currencies
=====================================
ReAct Agent avec mémoire
LLM : API Claude (Anthropic) ou TokenFactory ou Ollama local
Rôle : Analyse macro — CPI, Fed Funds, GDP, Unemployment, Yield
Output : signal (BUY/SELL/HOLD) + confidence + explication macro

Prerequisites:
  pip install langchain>=0.2.0 langchain-ollama langchain-core langgraph anthropic
  Set in .env:
    ANTHROPIC_API_KEY=...        # si FX_LLM_PROVIDER=claude
    TOKEN_FACTORY_API_KEY=...    # si FX_LLM_PROVIDER=tokenfactory
    FX_LLM_PROVIDER=claude       # claude | tokenfactory | local
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
from dotenv import load_dotenv

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
from langgraph.prebuilt import create_react_agent
import MetaTrader5 as mt5

warnings.filterwarnings("ignore")
load_dotenv()

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

SMALL_ACCOUNT_MODE             = os.getenv("FX_SMALL_ACCOUNT_MODE", "1").lower() in {"1","true","yes","on"}
SMALL_ACCOUNT_MAX_BALANCE      = float(os.getenv("FX_SMALL_ACCOUNT_MAX_BALANCE", "150"))
SMALL_ACCOUNT_MIN_MARGIN_LEVEL = float(os.getenv("FX_SMALL_ACCOUNT_MIN_MARGIN_LEVEL", "200"))
SMALL_ACCOUNT_MIN_FREE_MARGIN  = float(os.getenv("FX_SMALL_ACCOUNT_MIN_FREE_MARGIN", "20"))
SMALL_ACCOUNT_MAX_OPEN_POSITIONS = int(os.getenv("FX_SMALL_ACCOUNT_MAX_OPEN_POSITIONS", "1"))
SMALL_ACCOUNT_CONFIDENCE_CAP   = float(os.getenv("FX_SMALL_ACCOUNT_CONFIDENCE_CAP", "0.65"))

PAIRS          = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
DEFAULT_SYMBOL = os.getenv("FX_DEFAULT_SYMBOL", "EURUSD").upper()
RUN_ALL_SYMBOLS = os.getenv("FX_RUN_ALL_SYMBOLS", "0").lower() in {"1","true","yes","on"}

# Mapping paire → devises impactées
PAIR_CURRENCIES = {
    "EURUSD": {"base": "EUR", "quote": "USD", "macro_focus": ["US","EU"]},
    "USDJPY": {"base": "USD", "quote": "JPY", "macro_focus": ["US","JP"]},
    "GBPUSD": {"base": "GBP", "quote": "USD", "macro_focus": ["US","UK"]},
    "USDCHF": {"base": "USD", "quote": "CHF", "macro_focus": ["US","CH"]},
}

# ─────────────────────────────────────────
# HELPERS — LOAD MACRO DATA
# ─────────────────────────────────────────

def pg_connect():
    return psycopg2.connect(PG_DSN)


def load_macro_indicators(days: int = 365) -> pd.DataFrame:
    """Charge tous les indicateurs macro depuis PostgreSQL."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        conn = pg_connect()
        df   = pd.read_sql(
            f"""
            SELECT date, series_id, indicator_name, value
            FROM economic_indicators
            WHERE date >= '{since}'
            ORDER BY date DESC
            """,
            conn
        )
        conn.close()
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        print(f"   [WARN] PostgreSQL error: {e}")
        return pd.DataFrame()


def load_economic_events(days: int = 7) -> pd.DataFrame:
    """Charge les événements économiques récents et à venir."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        conn = pg_connect()
        df   = pd.read_sql(
            f"""
            SELECT event_date, currency, event_name, importance, forecast, actual, previous
            FROM economic_events
            WHERE event_date >= '{since}'
            ORDER BY event_date DESC
            LIMIT 50
            """,
            conn
        )
        conn.close()
        df["event_date"] = pd.to_datetime(df["event_date"])
        return df
    except Exception as e:
        print(f"   [WARN] Economic events error: {e}")
        return pd.DataFrame()


def load_news_sentiment(symbol: str, days: int = 3) -> pd.DataFrame:
    """Charge les news récentes liées à la paire."""
    currencies = PAIR_CURRENCIES.get(symbol, {})
    base  = currencies.get("base", "")
    quote = currencies.get("quote", "")
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        conn = pg_connect()
        df   = pd.read_sql(
            f"""
            SELECT title, source, published_at, currencies
            FROM news_articles
            WHERE published_at >= '{since}'
            AND (currencies @> ARRAY['{base}']::varchar[]
                 OR currencies @> ARRAY['{quote}']::varchar[])
            ORDER BY published_at DESC
            LIMIT 20
            """,
            conn
        )
        conn.close()
        return df
    except Exception as e:
        print(f"   [WARN] News error: {e}")
        return pd.DataFrame()


def get_mt5_account_snapshot() -> dict:
    """Return a compact MT5 account snapshot for risk-aware validation."""
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
            sym = getattr(pos, "symbol", "UNKNOWN")
            exposure[sym] = exposure.get(sym, 0) + float(getattr(pos, "volume", 0) or 0)
        return {
            "available":       True,
            "balance":         float(getattr(account, "balance", 0) or 0),
            "equity":          float(getattr(account, "equity", 0) or 0),
            "free_margin":     float(getattr(account, "margin_free", 0) or 0),
            "margin_level":    float(getattr(account, "margin_level", 0) or 0),
            "leverage":        int(getattr(account, "leverage", 0) or 0),
            "positions_count": len(positions),
            "symbol_exposure": exposure,
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}
    finally:
        if connected:
            mt5.shutdown()


def apply_small_account_risk_guard(signal_data: dict, account_snapshot: dict) -> dict:
    """Applique les guardrails pour petits comptes (identique à agent_technical)."""
    if not SMALL_ACCOUNT_MODE:
        signal_data["risk_mode"] = "disabled"
        return signal_data
    if not account_snapshot.get("available"):
        signal_data["risk_mode"] = "small_account_no_snapshot"
        return signal_data
    balance = float(account_snapshot.get("balance", 0) or 0)
    if balance > SMALL_ACCOUNT_MAX_BALANCE:
        signal_data["risk_mode"] = "standard"
        return signal_data

    signal     = str(signal_data.get("signal", "HOLD")).upper()
    confidence = float(signal_data.get("confidence", 0.5) or 0.5)
    free_margin    = float(account_snapshot.get("free_margin", 0) or 0)
    margin_level   = float(account_snapshot.get("margin_level", 0) or 0)
    positions_count = int(account_snapshot.get("positions_count", 0) or 0)
    reasons = []

    if confidence > SMALL_ACCOUNT_CONFIDENCE_CAP:
        confidence = SMALL_ACCOUNT_CONFIDENCE_CAP
        reasons.append("confidence capped for small account")
    if positions_count >= SMALL_ACCOUNT_MAX_OPEN_POSITIONS and signal in {"BUY","SELL"}:
        signal = "HOLD"; confidence = min(confidence, 0.45)
        reasons.append("max open positions reached")
    if free_margin < SMALL_ACCOUNT_MIN_FREE_MARGIN and signal in {"BUY","SELL"}:
        signal = "HOLD"; confidence = min(confidence, 0.40)
        reasons.append("free margin below threshold")
    if margin_level > 0 and margin_level < SMALL_ACCOUNT_MIN_MARGIN_LEVEL and signal in {"BUY","SELL"}:
        signal = "HOLD"; confidence = min(confidence, 0.40)
        reasons.append("margin level below threshold")

    signal_data["signal"]     = signal
    signal_data["confidence"] = round(confidence, 2)
    signal_data["risk_mode"]  = "small_account_100"
    signal_data["risk_constraints"] = {
        "max_balance":         SMALL_ACCOUNT_MAX_BALANCE,
        "min_margin_level":    SMALL_ACCOUNT_MIN_MARGIN_LEVEL,
        "min_free_margin":     SMALL_ACCOUNT_MIN_FREE_MARGIN,
        "max_open_positions":  SMALL_ACCOUNT_MAX_OPEN_POSITIONS,
        "confidence_cap":      SMALL_ACCOUNT_CONFIDENCE_CAP,
    }
    if reasons:
        signal_data["risk_adjustments"] = reasons
    return signal_data

# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────

@tool
def get_macro_indicators(symbol: str) -> str:
    """
    Get latest macroeconomic indicators (CPI, Fed Funds Rate, GDP, Unemployment,
    10Y Treasury, Inflation Expectations) relevant to a forex pair.
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        df = load_macro_indicators(days=400)
        if df.empty:
            return "No macro data available"

        # Dernière valeur par indicateur
        latest = df.groupby("series_id").first().reset_index()

        result = {}
        for _, row in latest.iterrows():
            sid  = row["series_id"]
            name = row["indicator_name"]
            val  = row["value"]
            date = str(row["date"])[:10]

            # Calcul de la variation (delta vs valeur précédente)
            history = df[df["series_id"] == sid].sort_values("date", ascending=False)
            delta   = None
            if len(history) >= 2:
                prev  = history.iloc[1]["value"]
                delta = round(float(val - prev), 4) if pd.notna(val) and pd.notna(prev) else None

            result[sid] = {
                "name":   name,
                "value":  round(float(val), 4) if pd.notna(val) else None,
                "date":   date,
                "delta":  delta,
                "trend":  "UP" if delta and delta > 0 else ("DOWN" if delta and delta < 0 else "FLAT"),
            }

        # Analyse macro contextuelle pour la paire
        pair_ctx = PAIR_CURRENCIES.get(symbol, {})
        result["pair_context"] = {
            "symbol":      symbol,
            "base":        pair_ctx.get("base", ""),
            "quote":       pair_ctx.get("quote", ""),
            "macro_focus": pair_ctx.get("macro_focus", []),
        }

        # Surprise macro (actual vs forecast) si disponible
        cpi  = result.get("CPIAUCSL", {})
        ff   = result.get("FEDFUNDS", {})
        real_rate = None
        if cpi.get("value") and ff.get("value"):
            real_rate = round(ff["value"] - cpi["value"], 4)
        result["derived"] = {
            "real_rate":          real_rate,
            "yield_curve_signal": "HAWKISH" if ff.get("delta",0) and ff["delta"] > 0 else "DOVISH",
        }

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_economic_events(symbol: str) -> str:
    """
    Get recent and upcoming high-impact economic events for currencies in a pair.
    Detects macro surprises (actual vs forecast).
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        df = load_economic_events(days=7)
        if df.empty:
            return json.dumps({"events": [], "message": "No recent economic events found"})

        # Filtrer par devise de la paire
        currencies = PAIR_CURRENCIES.get(symbol, {})
        base  = currencies.get("base", "")
        quote = currencies.get("quote", "")
        mask  = df["currency"].isin([base, quote, "USD", "EUR"])
        df    = df[mask].copy()

        events  = []
        surprises = []

        for _, row in df.iterrows():
            actual   = row.get("actual")
            forecast = row.get("forecast")
            previous = row.get("previous")

            surprise = None
            surprise_pct = None
            if pd.notna(actual) and pd.notna(forecast) and forecast != 0:
                surprise     = round(float(actual - forecast), 4)
                surprise_pct = round(float((actual - forecast) / abs(forecast) * 100), 2)

            event = {
                "date":       str(row["event_date"])[:16],
                "currency":   row["currency"],
                "event":      row["event_name"],
                "importance": row.get("importance", ""),
                "forecast":   float(actual)   if pd.notna(actual)   else None,
                "actual":     float(forecast)  if pd.notna(forecast)  else None,
                "previous":   float(previous) if pd.notna(previous) else None,
                "surprise":   surprise,
                "surprise_pct": surprise_pct,
                "direction":  "BEAT" if surprise and surprise > 0 else ("MISS" if surprise and surprise < 0 else "IN_LINE"),
            }
            events.append(event)

            if surprise and abs(surprise_pct or 0) > 5:
                surprises.append(f"{row['event_name']} ({row['currency']}): {event['direction']} by {surprise_pct}%")

        return json.dumps({
            "symbol":    symbol,
            "events":    events[:20],
            "surprises": surprises,
            "high_impact_count": sum(1 for e in events if e.get("importance","").lower() in ["high","red"]),
        }, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_rate_differential(symbol: str) -> str:
    """
    Compute interest rate differential between the two currencies of a pair.
    Rate differential is a key driver of forex trends (carry trade logic).
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        df = load_macro_indicators(days=60)
        if df.empty:
            return "No macro data"

        # Taux Fed Funds (USD)
        ff_df   = df[df["series_id"] == "FEDFUNDS"].sort_values("date", ascending=False)
        fed_rate = float(ff_df.iloc[0]["value"]) if not ff_df.empty else None

        # Taux 10Y (proxy du marché)
        y10_df   = df[df["series_id"] == "DGS10"].sort_values("date", ascending=False)
        yield_10y = float(y10_df.iloc[0]["value"]) if not y10_df.empty else None

        # Inflation expectations
        inf_df   = df[df["series_id"] == "T10YIE"].sort_values("date", ascending=False)
        inf_exp  = float(inf_df.iloc[0]["value"]) if not inf_df.empty else None

        pair_ctx = PAIR_CURRENCIES.get(symbol, {})

        result = {
            "symbol":          symbol,
            "base_currency":   pair_ctx.get("base", ""),
            "quote_currency":  pair_ctx.get("quote", ""),
            "fed_funds_rate":  fed_rate,
            "us_yield_10y":    yield_10y,
            "inflation_exp":   inf_exp,
            "real_yield":      round(yield_10y - inf_exp, 4) if yield_10y and inf_exp else None,
            "carry_signal":    None,
            "interpretation":  "",
        }

        # Logique carry trade simplifiée
        if fed_rate:
            if symbol in ["EURUSD", "GBPUSD"]:
                result["carry_signal"]   = "USD_BULLISH" if fed_rate > 3.0 else "USD_NEUTRAL"
                result["interpretation"] = (
                    f"High Fed rate ({fed_rate}%) favors USD strength → bearish {symbol}"
                    if fed_rate > 3.0
                    else f"Moderate Fed rate ({fed_rate}%) → neutral for {symbol}"
                )
            elif symbol == "USDJPY":
                result["carry_signal"]   = "JPY_BEARISH" if fed_rate > 1.0 else "JPY_BULLISH"
                result["interpretation"] = (
                    f"Fed rate ({fed_rate}%) >> BOJ rate → carry trade favors USDJPY UP"
                    if fed_rate > 1.0
                    else "Rate convergence → USDJPY pressure DOWN"
                )
            elif symbol == "USDCHF":
                result["carry_signal"]   = "CHF_NEUTRAL"
                result["interpretation"] = f"SNB follows Fed partially → neutral bias for USDCHF"

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_recent_news_macro(symbol: str) -> str:
    """
    Get recent forex news headlines related to a pair's currencies.
    Input: pair name, e.g. 'EURUSD'
    """
    try:
        symbol = symbol.strip().upper()
        df = load_news_sentiment(symbol, days=3)
        if df.empty:
            return json.dumps({"headlines": [], "message": "No recent news found"})

        headlines = []
        for _, row in df.iterrows():
            headlines.append({
                "title":  row["title"],
                "source": row["source"],
                "date":   str(row["published_at"])[:16],
            })

        return json.dumps({
            "symbol":    symbol,
            "count":     len(headlines),
            "headlines": headlines[:15],
        }, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


# ─────────────────────────────────────────
# TOOLS LIST
# ─────────────────────────────────────────

TOOLS = [
    get_macro_indicators,
    get_economic_events,
    get_rate_differential,
    get_recent_news_macro,
]

# ─────────────────────────────────────────
# MACRO AGENT CLASS
# ─────────────────────────────────────────

class MacroeconomicEventAgent:
    """
    ReAct Agent pour l'analyse macroéconomique.
    LLM : Claude API (raisonnement complexe) ou TokenFactory ou Ollama local.
    Mémoire : historique des 20 derniers messages.
    """

    def __init__(self):
        print("Initializing Macroeconomic Event Agent...")

        self.provider   = LLM_PROVIDER
        self.llm_model  = None
        self.llm        = None
        self.claude_client = None
        self.tf_client  = None

        if self.provider == "claude":
            if anthropic is None:
                raise RuntimeError("pip install anthropic required for FX_LLM_PROVIDER=claude")
            if not ANTHROPIC_API_KEY:
                raise RuntimeError("ANTHROPIC_API_KEY missing in .env")
            self.claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.llm_model     = ANTHROPIC_MODEL

        elif self.provider == "tokenfactory":
            if OpenAI is None:
                raise RuntimeError("pip install openai required for FX_LLM_PROVIDER=tokenfactory")
            if not TOKEN_FACTORY_API_KEY:
                raise RuntimeError("TOKEN_FACTORY_API_KEY missing in .env")
            self.tf_client = OpenAI(
                api_key=TOKEN_FACTORY_API_KEY,
                base_url=TOKEN_FACTORY_BASE_URL,
            )
            self.llm_model = TOKEN_FACTORY_MODEL

        else:  # local ollama
            self.llm = ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=0.1,
                num_predict=2048,
            )
            self.llm_model = OLLAMA_MODEL

        self.chat_history  = []
        self.signal_history = []

        print(f"   LLM  : {self.llm_model} ({self.provider})")
        print(f"   Tools: {[t.name for t in TOOLS]}")
        print("   [OK] Ready!\n")

    def _invoke_llm(self, messages: list, system: str = "") -> str:
        """Invoke le bon provider avec fallback Ollama."""

        # ── Claude API
        if self.provider == "claude":
            payload = []
            for m in messages:
                role = "user" if isinstance(m, HumanMessage) else "assistant"
                payload.append({"role": role, "content": m.content})
            response = self.claude_client.messages.create(
                model=self.llm_model,
                max_tokens=2048,
                system=system or "You are an expert macroeconomic analyst for Forex markets.",
                messages=payload,
            )
            return response.content[0].text

        # ── TokenFactory (OpenAI-compatible)
        if self.provider == "tokenfactory":
            payload = []
            if system:
                payload.append({"role": "system", "content": system})
            for m in messages:
                role = "user" if isinstance(m, HumanMessage) else "assistant"
                payload.append({"role": role, "content": m.content})
            response = self.tf_client.chat.completions.create(
                model=TOKEN_FACTORY_MODEL,
                messages=payload,
                temperature=0.1,
                max_tokens=2048,
            )
            return response.choices[0].message.content

        # ── Ollama local avec fallback
        tried = [OLLAMA_MODEL]
        try:
            return self.llm.invoke(messages).content
        except Exception as e:
            if "not found" not in str(e).lower() and "404" not in str(e):
                raise
            for model_name in OLLAMA_FALLBACK_MODELS:
                if model_name == OLLAMA_MODEL:
                    continue
                tried.append(model_name)
                try:
                    print(f"   [WARN] Trying fallback: {model_name}")
                    fb = ChatOllama(model=model_name, base_url=OLLAMA_BASE_URL, temperature=0.1)
                    result = fb.invoke(messages).content
                    self.llm = fb
                    print(f"   [OK] Fallback active: {model_name}")
                    return result
                except Exception:
                    continue
            raise RuntimeError(f"No Ollama model available. Tried: {', '.join(tried)}")

    def analyze(self, symbol: str) -> dict:
        print(f"\n{'='*55}\n  MACRO ANALYSIS — {symbol}\n{'='*55}")

        # ── STEP 1 : Collecte des vraies données macro
        print("   Collecting real macro data...")
        macro_data = get_macro_indicators.invoke(symbol)
        econ_events = get_economic_events.invoke(symbol)
        rate_diff   = get_rate_differential.invoke(symbol)
        news        = get_recent_news_macro.invoke(symbol)
        account_snapshot = get_mt5_account_snapshot()
        print("   [OK] Macro data collected")

        # ── STEP 2 : LLM synthèse macro
        system_prompt = (
            "You are a senior macroeconomic analyst specializing in Forex markets. "
            "You analyze CPI, interest rates, GDP, employment data, and yield curves "
            "to assess currency strength and generate directional trading signals. "
            "Always base your analysis strictly on the provided data."
        )

        synthesis_prompt = f"""
Analyze the macroeconomic environment for {symbol} and generate a trading signal.

MACRO INDICATORS (FRED data):
{macro_data}

ECONOMIC EVENTS & SURPRISES (last 7 days):
{econ_events}

RATE DIFFERENTIAL & CARRY TRADE ANALYSIS:
{rate_diff}

RECENT NEWS HEADLINES:
{news}

MT5 ACCOUNT SNAPSHOT:
{json.dumps(account_snapshot, indent=2)}

ANALYSIS FRAMEWORK:
1. Assess USD strength/weakness based on CPI trend, Fed rate direction, real yield
2. Evaluate the other currency (EUR/JPY/GBP/CHF) macro context
3. Check for macro surprises that could drive momentum
4. Consider rate differential (carry trade) direction
5. If small account detected, keep signal conservative

Provide:
1. Macro analysis (4-5 sentences covering the key drivers)
2. Rate differential assessment
3. Event risk summary
4. Final JSON signal:

```json
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0-1.0,
  "reasoning": "macro-driven explanation",
  "macro_bias": "USD_BULLISH" | "USD_BEARISH" | "NEUTRAL",
  "key_drivers": ["driver1", "driver2", "driver3"],
  "event_risk": "HIGH" | "MEDIUM" | "LOW",
  "rate_differential_signal": "BULLISH" | "BEARISH" | "NEUTRAL"
}}
```
Only use BUY, SELL, or HOLD. Be conservative if event risk is HIGH.
"""

        try:
            self.chat_history.append(HumanMessage(content=synthesis_prompt))
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]

            output = self._invoke_llm(self.chat_history, system=system_prompt)
            self.chat_history.append(AIMessage(content=output))

            print(f"\nLLM Macro Synthesis:\n{output[:600]}...")

            signal_data = self._parse_signal(output, symbol)
            signal_data = apply_small_account_risk_guard(signal_data, account_snapshot)
            signal_data.update({
                "timestamp": datetime.utcnow().isoformat(),
                "agent":     "macro",
                "raw_data":  {
                    "macro_indicators": macro_data,
                    "economic_events":  econ_events,
                    "rate_differential": rate_diff,
                    "news":             news,
                    "account_snapshot": account_snapshot,
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
                d = json.loads(m.group(1))
                d["symbol"] = symbol
                return d
            m = re.search(r'\{[^{}]*"signal"[^{}]*\}', output, re.DOTALL)
            if m:
                d = json.loads(m.group(0))
                d["symbol"] = symbol
                return d
        except Exception:
            pass
        signal = "HOLD"
        if "BUY"  in output.upper(): signal = "BUY"
        elif "SELL" in output.upper(): signal = "SELL"
        return {"symbol": symbol, "signal": signal, "confidence": 0.5, "reasoning": output[:400]}

    def _fallback_signal(self, symbol: str) -> dict:
        """Fallback basé sur les règles macro sans LLM."""
        print("   [WARN] Fallback: rule-based macro signal")
        try:
            df = load_macro_indicators(days=60)
            if df.empty:
                return {"symbol": symbol, "signal": "HOLD", "confidence": 0.0}

            ff_df    = df[df["series_id"] == "FEDFUNDS"].sort_values("date", ascending=False)
            cpi_df   = df[df["series_id"] == "CPIAUCSL"].sort_values("date", ascending=False)
            fed_rate = float(ff_df.iloc[0]["value"]) if not ff_df.empty else 0
            cpi_val  = float(cpi_df.iloc[0]["value"]) if not cpi_df.empty else 0
            cpi_delta = float(cpi_df.iloc[0]["value"] - cpi_df.iloc[1]["value"]) if len(cpi_df) >= 2 else 0

            # USD bullish si taux élevé et CPI en hausse
            usd_bull_score = sum([
                fed_rate > 4.0,
                cpi_delta > 0,
                fed_rate > cpi_val,
            ])

            if symbol in ["EURUSD", "GBPUSD"]:
                # USD fort → paire baisse
                if usd_bull_score >= 2: signal, conf = "SELL", 0.55
                else: signal, conf = "HOLD", 0.40
            elif symbol == "USDJPY":
                # USD fort → paire monte
                if usd_bull_score >= 2: signal, conf = "BUY", 0.55
                else: signal, conf = "HOLD", 0.40
            else:
                signal, conf = "HOLD", 0.40

            fallback = {
                "symbol": symbol, "signal": signal, "confidence": conf,
                "reasoning": f"Rule-based: fed_rate={fed_rate}, cpi_delta={cpi_delta:.4f}, usd_bull={usd_bull_score}/3",
                "macro_bias": "USD_BULLISH" if usd_bull_score >= 2 else "NEUTRAL",
            }
            return apply_small_account_risk_guard(fallback, get_mt5_account_snapshot())
        except Exception as e:
            return {"symbol": symbol, "signal": "HOLD", "confidence": 0.0, "reasoning": str(e)}

    def _save_signal(self, signal: dict, symbol: str):
        os.makedirs("outputs/signals", exist_ok=True)
        path = f"outputs/signals/macro_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        with open(path, "w") as f:
            json.dump(signal, f, indent=2, default=str)
        print(f"\n   Saved signal -> {path}")


# ─────────────────────────────────────────
# CLI HELPERS
# ─────────────────────────────────────────

def resolve_target_symbol() -> str:
    if len(sys.argv) > 1:
        candidate = sys.argv[1].upper().strip()
    else:
        candidate = DEFAULT_SYMBOL
    if candidate not in PAIRS:
        raise ValueError(f"Invalid symbol '{candidate}'. Allowed: {', '.join(PAIRS)}")
    return candidate


def should_run_all_symbols() -> bool:
    if RUN_ALL_SYMBOLS:
        return True
    if len(sys.argv) <= 1:
        return True
    return sys.argv[1].upper().strip() == "ALL"


def print_comparison_report(signals: list) -> None:
    if not signals:
        print("No signals generated.")
        return

    def sort_key(item):
        s = str(item.get("signal","HOLD")).upper()
        rank = {"BUY":0,"SELL":1,"HOLD":2}.get(s, 3)
        return (rank, -float(item.get("confidence",0) or 0))

    ranked = sorted(signals, key=sort_key)
    print(f"\n{'='*72}\n  MACRO MULTI-PAIR REPORT\n{'='*72}")
    for item in ranked:
        sym  = item.get("symbol","?")
        sig  = item.get("signal","HOLD")
        conf = float(item.get("confidence",0) or 0)
        bias = item.get("macro_bias","N/A")
        risk = item.get("event_risk","N/A")
        print(f"  {sym:<6} -> {sig:<4} ({conf:.0%}) | macro_bias={bias} | event_risk={risk}")

    best = ranked[0]
    print(f"\n  Best candidate: {best.get('symbol','?')} -> {best.get('signal','HOLD')} ({float(best.get('confidence',0) or 0):.0%})")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("="*55)
    print("  MACROECONOMIC EVENT AGENT")
    print("  FX-AlphaLab | Major Currencies")
    print("="*55)
    print(f"\n  Provider : {LLM_PROVIDER}")
    print(f"  Model    : {ANTHROPIC_MODEL if LLM_PROVIDER=='claude' else (TOKEN_FACTORY_MODEL if LLM_PROVIDER=='tokenfactory' else OLLAMA_MODEL)}\n")

    agent = MacroeconomicEventAgent()

    if should_run_all_symbols():
        print("   Mode: ALL pairs")
        signals = [agent.analyze(sym) for sym in PAIRS]
        print_comparison_report(signals)
    else:
        symbol = resolve_target_symbol()
        print(f"   Target: {symbol}")
        signal = agent.analyze(symbol)
        conf = float(signal.get("confidence", 0) or 0)
        print(f"\n{'='*55}")
        print(f"  RESULT : {signal.get('signal')}  ({conf:.0%})")
        print(f"  Bias   : {signal.get('macro_bias','N/A')}")
        print(f"  Risk   : {signal.get('event_risk','N/A')}")
        print(f"  Reason : {str(signal.get('reasoning',''))[:200]}")
        print(f"{'='*55}")
