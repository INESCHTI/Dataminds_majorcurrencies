"""
=====================================
TECHNICAL PATTERN AGENT v2
FX-AlphaLab | Major Currencies
=====================================
ReAct Agent avec mémoire
LLM : Ollama (Mistral 7B local)
Rôle : Analyse technique multi-timeframe
Output : signal (BUY/SELL/HOLD) + confidence + explication

Prerequisites:
  pip install langchain>=0.2.0 langchain-ollama langchain-core langgraph
  ollama pull mistral
"""

import os
import json
import re
import warnings
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from influxdb_client import InfluxDBClient

warnings.filterwarnings("ignore")


def load_environment_files() -> None:
    """Load local env files with a few encoding fallbacks."""
    env_dir = Path(__file__).resolve().parent
    root_dir = env_dir.parent
    env_files = [root_dir / ".env", env_dir / ".env", env_dir / ".env.local"]
    encodings = ["utf-8", "utf-8-sig", "utf-16"]

    for env_file in env_files:
        if not env_file.exists():
            continue

        loaded = False
        for encoding in encodings:
            try:
                if load_dotenv(dotenv_path=env_file, encoding=encoding, override=True):
                    loaded = True
                    break
            except UnicodeDecodeError:
                continue

        if not loaded:
            print(f"   [WARN] Could not load {env_file.name} with supported encodings")


load_environment_files()

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
FX_LLM_PROVIDER = os.getenv("FX_LLM_PROVIDER", "local").strip().lower()

TOKEN_FACTORY_BASE_URL = os.getenv("TOKEN_FACTORY_BASE_URL", "https://tokenfactory.esprit.tn/api")
TOKEN_FACTORY_MODEL = os.getenv("TOKEN_FACTORY_MODEL", "hosted_vllm/Llama-3.1-70B-Instruct")
TOKEN_FACTORY_API_KEY = os.getenv("TOKEN_FACTORY_API_KEY")

INFLUX_CLIENT = InfluxDBClient(
    url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
    token=os.getenv("INFLUXDB_TOKEN", ""),
    org=os.getenv("INFLUXDB_ORG", ""),
)
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "forex_data")

PAIRS = [
    "EURUSD", "USDCHF", "GBPUSD", "USDJPY",
]
TIMEFRAMES = ["1H", "4H", "1D"]
DEFAULT_SYMBOL = os.getenv("FX_DEFAULT_SYMBOL", "EURUSD").upper()

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def load_latest_ohlc(symbol: str, timeframe: str, n: int = 100) -> pd.DataFrame:
    """Charge les N dernières bougies depuis InfluxDB."""
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -30d)
      |> filter(fn: (r) => r._measurement == "forex_prices")
      |> filter(fn: (r) => r.symbol == "{symbol}")
      |> filter(fn: (r) => r.timeframe == "{timeframe}")
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: {n})
      |> sort(columns: ["_time"])
    '''
    try:
        df = INFLUX_CLIENT.query_api().query_data_frame(query)
        if df.empty:
            return pd.DataFrame()
        df = df[["_time", "open", "high", "low", "close", "volume"]].copy()
        df.rename(columns={"_time": "time"}, inplace=True)
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)
        return df.astype(float)
    except Exception as e:
        print(f"   [WARN] InfluxDB error: {e}")
        return pd.DataFrame()


def compute_indicators(df: pd.DataFrame) -> dict:
    """Calcule les indicateurs techniques."""
    if df.empty or len(df) < 20:
        return {}

    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]

    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rsi = (100 - 100 / (1 + gain / (loss + 1e-10))).iloc[-1]

    ema12 = c.ewm(span=12).mean()
    ema26 = c.ewm(span=26).mean()
    macd = (ema12 - ema26).iloc[-1]
    macd_sig = (ema12 - ema26).ewm(span=9).mean().iloc[-1]

    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    bb_upper = (sma20 + 2 * std20).iloc[-1]
    bb_lower = (sma20 - 2 * std20).iloc[-1]
    bb_pct = (c.iloc[-1] - bb_lower) / (bb_upper - bb_lower + 1e-10)
    bb_width = (bb_upper - bb_lower) / sma20.iloc[-1]

    atr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1).rolling(14).mean().iloc[-1]

    sma10 = c.rolling(10).mean().iloc[-1]
    sma20v = c.rolling(20).mean().iloc[-1]
    sma50 = c.rolling(50).mean().iloc[-1]

    vol_sma20 = v.rolling(20).mean().iloc[-1]
    vol_ratio = v.iloc[-1] / (vol_sma20 + 1e-10)

    price = c.iloc[-1]
    prev = c.iloc[-2]

    return {
        "price": round(float(price), 5),
        "change_pct": round(float((price - prev) / prev * 100), 4),
        "rsi": round(float(rsi), 2),
        "macd": round(float(macd), 6),
        "macd_signal": round(float(macd_sig), 6),
        "macd_hist": round(float(macd - macd_sig), 6),
        "bb_pct": round(float(bb_pct), 4),
        "bb_width": round(float(bb_width), 4),
        "atr": round(float(atr), 6),
        "sma10": round(float(sma10), 5),
        "sma20": round(float(sma20v), 5),
        "sma50": round(float(sma50), 5),
        "vol_ratio": round(float(vol_ratio), 3),
        "price_vs_sma50": round(float((price - sma50) / sma50 * 100), 4),
        "trend_short": "BULLISH" if sma10 > sma20v else "BEARISH",
        "trend_long": "BULLISH" if sma20v > sma50 else "BEARISH",
    }


# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────

@tool
def get_technical_indicators(symbol_tf: str) -> str:
    """Get technical indicators for a forex pair and timeframe, e.g. 'EURUSD 1H'."""
    try:
        parts = symbol_tf.strip().split()
        symbol = parts[0].upper()
        tf = parts[1].upper() if len(parts) > 1 else "1H"
        if symbol not in PAIRS:
            return f"Error: {symbol} not in {PAIRS}"
        df = load_latest_ohlc(symbol, tf)
        if df.empty:
            return f"No data for {symbol} {tf}"
        ind = compute_indicators(df)
        ind.update({"symbol": symbol, "timeframe": tf, "timestamp": datetime.utcnow().isoformat()})
        return json.dumps(ind, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_multi_timeframe_analysis(symbol: str) -> str:
    """Analyze a forex pair across 3 timeframes (1H, 4H, 1D)."""
    try:
        symbol = symbol.strip().upper()
        if symbol not in PAIRS:
            return f"Error: {symbol} not in {PAIRS}"
        result = {}
        for tf in TIMEFRAMES:
            df = load_latest_ohlc(symbol, tf)
            if not df.empty:
                ind = compute_indicators(df)
                result[tf] = {
                    "trend": ind.get("trend_long", "N/A"),
                    "rsi": ind.get("rsi", 0),
                    "macd_pos": ind.get("macd", 0) > ind.get("macd_signal", 0),
                    "bb_pct": ind.get("bb_pct", 0.5),
                    "price": ind.get("price", 0),
                }
        bullish = sum(1 for d in result.values() if d.get("trend") == "BULLISH")
        result["confluence"] = {
            "bullish_timeframes": bullish,
            "direction": "BULLISH" if bullish >= 2 else "BEARISH",
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool
def detect_chart_patterns(symbol_tf: str) -> str:
    """Detect candlestick and chart patterns."""
    try:
        parts = symbol_tf.strip().split()
        symbol = parts[0].upper()
        tf = parts[1].upper() if len(parts) > 1 else "1H"
        df = load_latest_ohlc(symbol, tf, n=50)
        if df.empty or len(df) < 10:
            return "Insufficient data"

        c, o, h, l = df["close"], df["open"], df["high"], df["low"]
        patterns = []
        body = (c - o).abs()
        rng = h - l

        if (body / (rng + 1e-10)).iloc[-1] < 0.1:
            patterns.append("DOJI - indecision, possible reversal")
        if c.iloc[-1] > o.iloc[-1] and c.iloc[-2] < o.iloc[-2] and c.iloc[-1] > o.iloc[-2] and o.iloc[-1] < c.iloc[-2]:
            patterns.append("BULLISH ENGULFING - reversal UP")
        if c.iloc[-1] < o.iloc[-1] and c.iloc[-2] > o.iloc[-2] and c.iloc[-1] < o.iloc[-2] and o.iloc[-1] > c.iloc[-2]:
            patterns.append("BEARISH ENGULFING - reversal DOWN")
        if h.iloc[-5:].is_monotonic_increasing and l.iloc[-5:].is_monotonic_increasing:
            patterns.append("HIGHER HIGHS + HIGHER LOWS - strong uptrend")
        elif h.iloc[-5:].is_monotonic_decreasing and l.iloc[-5:].is_monotonic_decreasing:
            patterns.append("LOWER HIGHS + LOWER LOWS - strong downtrend")

        ind = compute_indicators(df)
        rsi = ind.get("rsi", 50)
        if rsi < 30:
            patterns.append(f"RSI OVERSOLD ({rsi:.1f}) - BUY zone")
        elif rsi > 70:
            patterns.append(f"RSI OVERBOUGHT ({rsi:.1f}) - SELL zone")
        if ind.get("bb_width", 1) < 0.005:
            patterns.append("BOLLINGER SQUEEZE - breakout incoming")

        return json.dumps({
            "symbol": symbol,
            "timeframe": tf,
            "patterns": patterns or ["No significant pattern"],
            "candles_analyzed": len(df),
        }, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_support_resistance(symbol_tf: str) -> str:
    """Calculate key support and resistance levels using pivot points."""
    try:
        parts = symbol_tf.strip().split()
        symbol = parts[0].upper()
        tf = parts[1].upper() if len(parts) > 1 else "1D"
        df = load_latest_ohlc(symbol, tf, n=200)
        if df.empty:
            return "No data"

        price = df["close"].iloc[-1]
        prev_h = df["high"].iloc[-2]
        prev_l = df["low"].iloc[-2]
        prev_c = df["close"].iloc[-2]
        pivot = (prev_h + prev_l + prev_c) / 3
        r1 = 2 * pivot - prev_l
        r2 = pivot + (prev_h - prev_l)
        s1 = 2 * pivot - prev_h
        s2 = pivot - (prev_h - prev_l)

        return json.dumps({
            "symbol": symbol,
            "timeframe": tf,
            "price": round(float(price), 5),
            "pivot": round(float(pivot), 5),
            "R1": round(float(r1), 5),
            "R2": round(float(r2), 5),
            "S1": round(float(s1), 5),
            "S2": round(float(s2), 5),
            "pips_to_R1": round(abs(r1 - price) * 10000, 1),
            "pips_to_S1": round(abs(price - s1) * 10000, 1),
        }, indent=2)
    except Exception as e:
        return f"Error: {e}"


TOOLS = [get_technical_indicators, get_multi_timeframe_analysis, detect_chart_patterns, get_support_resistance]


# ─────────────────────────────────────────
# AGENT CLASS
# ─────────────────────────────────────────

class TechnicalPatternAgent:
    def __init__(self):
        print("Initializing Technical Pattern Agent (v2)...")

        self.provider = FX_LLM_PROVIDER
        self.llm = None

        if self.provider == "tokenfactory":
            if OpenAI is None:
                raise RuntimeError("openai package is required for FX_LLM_PROVIDER=tokenfactory")
            if not TOKEN_FACTORY_API_KEY:
                raise RuntimeError("TOKEN_FACTORY_API_KEY is required for FX_LLM_PROVIDER=tokenfactory")
            self.llm_client = OpenAI(
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
            self.agent = create_react_agent(
                model=self.llm,
                tools=TOOLS,
            )
            self.llm_model = OLLAMA_MODEL

        self.chat_history = []
        self.signal_history = []

        print(f"   LLM  : {self.llm_model} ({self.provider})")
        print(f"   Tools: {[t.name for t in TOOLS]}")
        print("   [OK] Ready!\n")

    def _call_llm(self, messages):
        if self.provider == "tokenfactory":
            payload = []
            for message in messages:
                role = getattr(message, "type", "user")
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
                elif role not in {"system", "user", "assistant"}:
                    role = "user"
                payload.append({"role": role, "content": message.content})

            response = self.llm_client.chat.completions.create(
                model=TOKEN_FACTORY_MODEL,
                messages=payload,
                temperature=0.1,
                max_tokens=2048,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            return response.choices[0].message.content

        return self.llm.invoke(messages).content

    def analyze(self, symbol: str) -> dict:
        print(f"\n{'='*55}\n  TECHNICAL ANALYSIS - {symbol}\n{'='*55}")

        print("   Collecting real data from tools...")
        mtf = get_multi_timeframe_analysis.invoke(symbol)
        ind = get_technical_indicators.invoke(f"{symbol} 1H")
        pat = detect_chart_patterns.invoke(f"{symbol} 1H")
        sr = get_support_resistance.invoke(f"{symbol} 1D")

        print("   [OK] Data collected")

        synthesis_prompt = f"""
You are an expert Forex technical analyst. Based on the REAL data below,
generate a trading signal for {symbol}.

MULTI-TIMEFRAME ANALYSIS:
{mtf}

TECHNICAL INDICATORS (1H):
{ind}

CHART PATTERNS (1H):
{pat}

SUPPORT & RESISTANCE (1D):
{sr}

Based on this real data, provide:
1. A brief analysis (3-4 sentences)
2. A final JSON signal block like this:
```json
{{
  "signal": "BUY",
  "confidence": 0.72,
  "reasoning": "explain why based on the data above",
  "entry_zone": "price from the data",
  "stop_loss": "S1 level from data",
  "take_profit": "R1 level from data"
}}
```
Only use BUY, SELL, or HOLD. Base everything strictly on the data provided.
"""

        try:
            self.chat_history.append(HumanMessage(content=synthesis_prompt))
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]

            output = self._call_llm(self.chat_history)
            self.chat_history.append(AIMessage(content=output))

            print(f"\nLLM Synthesis:\n{output[:600]}...")

            signal_data = self._parse_signal(output, symbol)
            signal_data.update({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "technical",
                "raw_data": {
                    "multi_timeframe": mtf,
                    "indicators_1h": ind,
                    "patterns": pat,
                    "support_resistance": sr,
                },
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
        if "BUY" in output.upper():
            signal = "BUY"
        elif "SELL" in output.upper():
            signal = "SELL"
        return {"symbol": symbol, "signal": signal, "confidence": 0.5, "reasoning": output[:400]}

    def _fallback_signal(self, symbol: str) -> dict:
        print("   [WARN] Fallback: direct computation (no LLM)")
        df = load_latest_ohlc(symbol, "1H")
        if df.empty:
            return {"symbol": symbol, "signal": "HOLD", "confidence": 0.0}
        ind = compute_indicators(df)
        rsi = ind.get("rsi", 50)
        bull = sum([
            rsi < 50,
            ind.get("macd", 0) > ind.get("macd_signal", 0),
            ind.get("bb_pct", 0.5) < 0.5,
            ind.get("trend_long") == "BULLISH",
        ])
        if bull >= 3:
            signal, conf = "BUY", round(0.55 + (bull - 3) * 0.1, 2)
        elif bull <= 1:
            signal, conf = "SELL", round(0.55 + (1 - bull) * 0.1, 2)
        else:
            signal, conf = "HOLD", 0.40
        return {
            "symbol": symbol,
            "signal": signal,
            "confidence": conf,
            "reasoning": f"RSI={rsi:.1f}, bull_score={bull}/4",
            "key_indicators": ind,
        }

    def _save_signal(self, signal: dict, symbol: str):
        os.makedirs("outputs/signals", exist_ok=True)
        path = f"outputs/signals/technical_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(signal, f, indent=2, default=str)
        print(f"\n   Saved signal -> {path}")


if __name__ == "__main__":
    print("=" * 55)
    print("  TECHNICAL PATTERN AGENT v2")
    print("  FX-AlphaLab | Major Currencies")
    print("=" * 55)
    print("\n[WARN] Prerequisites:")
    print("   ollama pull mistral  (then keep Ollama running)")
    print("   pip install langchain>=0.2.0 langchain-ollama\n")

    print(f"   LLM = {FX_LLM_PROVIDER}")
    if FX_LLM_PROVIDER == "tokenfactory":
        print(f"   Token Factory model = {TOKEN_FACTORY_MODEL}")
    else:
        print(f"   Ollama model = {OLLAMA_MODEL}")

    agent = TechnicalPatternAgent()
    print("\nSupported currencies:")
    for index, pair in enumerate(PAIRS, start=1):
        print(f"  {index}. {pair}")

    print("\nRunning all pairs automatically...\n")
    signals = []
    for symbol in PAIRS:
        print(f"   Running: {symbol}")
        signals.append(agent.analyze(symbol))

    print(f"\n{'='*55}")
    print("  RESULTS SUMMARY")
    print(f"{'='*55}")
    for item in signals:
        print(f"  {item.get('symbol')} -> {item.get('signal')} ({item.get('confidence', 0):.0%})")
    INFLUX_CLIENT.close()
