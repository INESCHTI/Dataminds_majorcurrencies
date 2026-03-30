import json
import os
from typing import Dict, List, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import storage

VALID_SYMBOLS = {"EURUSD", "USDJPY", "GBPUSD", "USDCHF"}
VALID_TIMEFRAMES = {"LIVE", "1S", "1H", "4H", "1D"}
VALID_SIDES = {"BUY", "SELL"}

router = APIRouter(prefix="/api/testing", tags=["testing"])


class CreateTradeRequest(BaseModel):
    session_id: str = Field(default="default", min_length=1, max_length=128)
    symbol: str = Field(..., min_length=3, max_length=16)
    side: str = Field(..., min_length=3, max_length=8)
    timeframe: str = Field(default="1H", min_length=2, max_length=8)
    size: float = Field(default=1.0, gt=0)
    entry_price: float = Field(..., gt=0)
    note: str = Field(default="", max_length=1000)
    agent_snapshot: Optional[Dict] = None


class CloseTradeRequest(BaseModel):
    close_price: float = Field(..., gt=0)


class ResetSessionRequest(BaseModel):
    session_id: str = Field(default="default", min_length=1, max_length=128)


class CoachSignal(BaseModel):
    trade_id: str = Field(..., min_length=4, max_length=80)
    symbol: str = Field(..., min_length=3, max_length=16)
    action: str = Field(..., min_length=4, max_length=20)
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    detail: str = Field(default="", max_length=1000)
    priority: int = Field(default=1, ge=0, le=1000)


class CoachAdviceRequest(BaseModel):
    session_id: str = Field(default="default", min_length=1, max_length=128)
    mode: str = Field(default="beginner", min_length=3, max_length=16)
    signals: List[CoachSignal] = Field(default_factory=list)


def _fallback_coach_message(signal: CoachSignal, mode: str) -> str:
    action = signal.action.upper()
    mode = (mode or "beginner").lower()
    short = mode == "advanced"
    if action == "CLOSE_NOW":
        return "Risk control first. Close this trade now to protect capital and wait for a cleaner setup."
    if action == "TAKE_PARTIAL":
        return "Momentum is in your favor. Take partial profits and trail your stop to defend gains."
    if action == "PREPARE":
        return "Stay alert. If momentum fades, tighten the stop or scale out to reduce giveback risk."
    if short:
        return "No high-priority trigger yet. Hold and follow your plan."
    return "No urgent trigger yet. Keep following your stop and target plan with patience."


def _maybe_llm_coach_message(signal: CoachSignal, mode: str) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "8"))
    action = signal.action.upper()
    tone = "very concise professional trader tone" if (mode or "beginner").lower() == "advanced" else "friendly coaching tone for a beginner"

    prompt = (
        "You are a trading coach assistant. "
        "Write ONE short actionable message (max 28 words). "
        "Do not promise profit. Mention uncertainty naturally. "
        f"Action={action}; Symbol={signal.symbol}; Confidence={signal.confidence:.2f}; Priority={signal.priority}; "
        f"CurrentDetail={signal.detail}; Tone={tone}."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return plain text only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 80,
    }

    req = urllib_request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return content[:280] if content else None
    except (urllib_error.URLError, urllib_error.HTTPError, TimeoutError, ValueError, KeyError):
        return None


@router.get("/trades")
async def get_trades(session_id: Optional[str] = None, status: Optional[str] = None):
    if status and status.upper() not in {"OPEN", "CLOSED"}:
        raise HTTPException(status_code=400, detail="status must be OPEN or CLOSED")
    return {
        "trades": storage.list_trades(session_id=session_id, status=status),
        "count": len(storage.list_trades(session_id=session_id, status=status)),
    }


@router.post("/trades")
async def post_trade(body: CreateTradeRequest):
    symbol = body.symbol.upper()
    side = body.side.upper()
    timeframe = body.timeframe.upper()

    if symbol not in VALID_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Unsupported symbol: {symbol}")
    if side not in VALID_SIDES:
        raise HTTPException(status_code=400, detail=f"Unsupported side: {side}")
    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Unsupported timeframe: {timeframe}")

    trade = storage.create_trade(
        {
            "session_id": body.session_id,
            "symbol": symbol,
            "side": side,
            "timeframe": timeframe,
            "size": body.size,
            "entry_price": body.entry_price,
            "note": body.note,
            "agent_snapshot": body.agent_snapshot or {},
        }
    )
    return trade


@router.patch("/trades/{trade_id}/close")
async def patch_close_trade(trade_id: str, body: CloseTradeRequest):
    try:
        trade = storage.close_trade(trade_id, body.close_price)
        return trade
    except KeyError:
        raise HTTPException(status_code=404, detail="Trade not found")


@router.get("/summary")
async def get_summary(session_id: Optional[str] = None):
    return storage.summary(session_id=session_id)


@router.post("/reset")
async def post_reset_session(body: ResetSessionRequest):
    result = storage.reset_session(body.session_id)
    return {
        "ok": True,
        **result,
    }


@router.post("/coach")
async def post_coach_advice(body: CoachAdviceRequest):
    signals = sorted(body.signals, key=lambda s: s.priority, reverse=True)[:4]
    advice = []

    for signal in signals:
        message = _maybe_llm_coach_message(signal, body.mode)
        llm_used = bool(message)
        if not message:
            message = _fallback_coach_message(signal, body.mode)
        advice.append(
            {
                "trade_id": signal.trade_id,
                "symbol": signal.symbol,
                "action": signal.action.upper(),
                "confidence": round(float(signal.confidence), 4),
                "priority": int(signal.priority),
                "message": message,
                "llm_used": llm_used,
            }
        )

    return {
        "session_id": body.session_id,
        "mode": body.mode,
        "advice": advice,
    }
