from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from .toolset import PAIRS, freshness_health, fuse_sentiment_technical, sentiment_snapshot, technical_snapshot

try:
    from langchain_ollama import ChatOllama

    OLLAMA_AVAILABLE = True
except Exception:
    ChatOllama = None
    OLLAMA_AVAILABLE = False


ToolFn = Callable[..., Any]


@dataclass
class AgentRun:
    method: str
    question: str
    pair: str
    selected_tools: list[str]
    tool_outputs: list[dict[str, Any]]
    final_decision: dict[str, Any]
    duration_ms: int


def _extract_pair(question: str) -> str:
    q = question.upper()
    for p in PAIRS:
        if p in q:
            return p
        if f"{p[:3]}/{p[3:]}" in q:
            return p
    return "EURUSD"


def _tool_registry() -> dict[str, ToolFn]:
    return {
        "technical_snapshot": technical_snapshot,
        "sentiment_snapshot": sentiment_snapshot,
        "freshness_health": freshness_health,
        "fuse_sentiment_technical": fuse_sentiment_technical,
    }


def _execute(selected: list[str], pair: str, api_base: str) -> list[dict[str, Any]]:
    tools = _tool_registry()
    out = []
    for name in selected:
        fn = tools[name]
        if name in {"technical_snapshot", "fuse_sentiment_technical"}:
            res = fn(pair, api_base=api_base)
        elif name == "freshness_health":
            res = fn(api_base=api_base)
        else:
            res = fn(pair)
        out.append({
            "name": res.name,
            "ok": res.ok,
            "payload": res.payload,
            "error": res.error,
        })
    return out


def _synthesize(outputs: list[dict[str, Any]], pair: str) -> dict[str, Any]:
    fusion = next((o for o in outputs if o["name"] == "fuse_sentiment_technical" and o["ok"]), None)
    if fusion:
        return {
            "pair": pair,
            "decision": fusion["payload"].get("decision", "NEUTRAL"),
            "fusion_score": fusion["payload"].get("fusion_score", 0.0),
            "reason": "Combined sentiment + technical",
        }

    tech = next((o for o in outputs if o["name"] == "technical_snapshot" and o["ok"]), None)
    sent = next((o for o in outputs if o["name"] == "sentiment_snapshot" and o["ok"]), None)

    if tech:
        return {
            "pair": pair,
            "decision": str(tech["payload"].get("signal", "NEUTRAL")).upper(),
            "fusion_score": float(tech["payload"].get("confidence", 0.0) or 0.0),
            "reason": "Technical-only fallback",
        }
    if sent:
        return {
            "pair": pair,
            "decision": str(sent["payload"].get("signal", "NEUTRAL")).upper(),
            "fusion_score": float(sent["payload"].get("confidence", 0.0) or 0.0),
            "reason": "Sentiment-only fallback",
        }

    return {
        "pair": pair,
        "decision": "NEUTRAL",
        "fusion_score": 0.0,
        "reason": "No tool data available",
    }


def run_rule_based(question: str, api_base: str = "http://localhost:3000") -> AgentRun:
    started = time.time()
    pair = _extract_pair(question)
    q = question.lower()

    selected = []
    if any(k in q for k in ["latence", "fresh", "fraicheur", "delay"]):
        selected.append("freshness_health")

    if any(k in q for k in ["combine", "fusion", "sentiment", "technique", "technical"]):
        selected.append("fuse_sentiment_technical")
    else:
        if any(k in q for k in ["sentiment", "news", "nlp"]):
            selected.append("sentiment_snapshot")
        if any(k in q for k in ["technique", "technical", "signal", "rsi", "macd"]):
            selected.append("technical_snapshot")

    if not selected:
        selected = ["fuse_sentiment_technical"]

    outputs = _execute(selected, pair, api_base)
    decision = _synthesize(outputs, pair)

    return AgentRun(
        method="rule_based",
        question=question,
        pair=pair,
        selected_tools=selected,
        tool_outputs=outputs,
        final_decision=decision,
        duration_ms=int((time.time() - started) * 1000),
    )


def _train_intent_model() -> tuple[TfidfVectorizer, LogisticRegression]:
    samples = [
        ("donne moi un signal technique eurusd", "tech"),
        ("analyse rsi et macd sur usdjpy", "tech"),
        ("quel est le sentiment news gbpusd", "sent"),
        ("analyse sentiment nlp sur usdchf", "sent"),
        ("combine sentiment et technique eurusd", "fusion"),
        ("fusionner analyses technique news", "fusion"),
        ("quelle est la latence de la source", "fresh"),
        ("etat fraicheur des donnees", "fresh"),
    ]
    X = [s[0] for s in samples]
    y = [s[1] for s in samples]

    vec = TfidfVectorizer(ngram_range=(1, 2))
    XX = vec.fit_transform(X)
    clf = LogisticRegression(max_iter=500, random_state=42)
    clf.fit(XX, y)
    return vec, clf


def run_nlp_router(question: str, api_base: str = "http://localhost:3000") -> AgentRun:
    started = time.time()
    pair = _extract_pair(question)

    vec, clf = _train_intent_model()
    label = clf.predict(vec.transform([question]))[0]

    mapping = {
        "tech": ["technical_snapshot"],
        "sent": ["sentiment_snapshot"],
        "fusion": ["fuse_sentiment_technical"],
        "fresh": ["freshness_health", "fuse_sentiment_technical"],
    }
    selected = mapping.get(label, ["fuse_sentiment_technical"])

    outputs = _execute(selected, pair, api_base)
    decision = _synthesize(outputs, pair)

    return AgentRun(
        method="nlp_router",
        question=question,
        pair=pair,
        selected_tools=selected,
        tool_outputs=outputs,
        final_decision=decision,
        duration_ms=int((time.time() - started) * 1000),
    )


def run_llm_langchain_router(question: str, api_base: str = "http://localhost:3000", model: str = "qwen2.5") -> AgentRun:
    started = time.time()
    pair = _extract_pair(question)

    # If LangChain+Ollama is unavailable, fallback to deterministic policy.
    if not OLLAMA_AVAILABLE:
        fallback = run_rule_based(question, api_base=api_base)
        fallback.method = "llm_langchain_router_fallback"
        return fallback

    prompt = (
        "You are an execution planner. Return JSON only with key 'tools' as list. "
        "Allowed tools: technical_snapshot, sentiment_snapshot, freshness_health, fuse_sentiment_technical. "
        "Prefer fuse_sentiment_technical when both sentiment and technical are relevant. "
        f"Question: {question}"
    )

    selected: list[str] = []
    try:
        llm = ChatOllama(model=model, temperature=0)
        raw = llm.invoke(prompt)
        content = str(getattr(raw, "content", raw)).strip()
        parsed = json.loads(content)
        tools = parsed.get("tools", []) if isinstance(parsed, dict) else []
        if isinstance(tools, list):
            selected = [t for t in tools if t in _tool_registry()]
    except Exception:
        selected = []

    if not selected:
        selected = ["fuse_sentiment_technical"]

    outputs = _execute(selected, pair, api_base)
    decision = _synthesize(outputs, pair)

    return AgentRun(
        method="llm_langchain_router",
        question=question,
        pair=pair,
        selected_tools=selected,
        tool_outputs=outputs,
        final_decision=decision,
        duration_ms=int((time.time() - started) * 1000),
    )
