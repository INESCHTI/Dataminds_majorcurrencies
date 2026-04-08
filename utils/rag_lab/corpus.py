from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class TextDocument:
    doc_id: str
    source: str
    title: str
    text: str
    symbol: str
    timestamp: str | None = None


def _safe_json_load(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        return None


def _iter_signal_files(signals_dir: Path) -> Iterable[Path]:
    if not signals_dir.exists():
        return []
    files = [p for p in signals_dir.glob("*.json") if p.is_file()]
    files.sort()
    return files


def load_documents_from_signals(signals_dir: str | Path, max_docs: int = 400) -> list[TextDocument]:
    base = Path(signals_dir)
    docs: list[TextDocument] = []

    for file_path in _iter_signal_files(base)[-max_docs:]:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        symbol = str(payload.get("symbol", "UNKNOWN")).upper()
        signal = str(payload.get("signal", "NEUTRAL"))
        confidence = payload.get("confidence", None)
        reasoning = str(payload.get("reasoning", "")).strip()
        timestamp = payload.get("timestamp")
        agent = str(payload.get("agent", file_path.stem.split("_", 1)[0]))

        fragments = [
            f"agent={agent}",
            f"symbol={symbol}",
            f"signal={signal}",
            f"confidence={confidence}",
            reasoning,
        ]

        raw_data = payload.get("raw_data")
        if isinstance(raw_data, dict):
            score_blob = raw_data.get("sentiment_scores")
            parsed = _safe_json_load(score_blob) if isinstance(score_blob, str) else None
            if isinstance(parsed, dict):
                top_articles = parsed.get("top_articles", [])
                if isinstance(top_articles, list):
                    top_titles = [str(a.get("title", "")) for a in top_articles[:5] if isinstance(a, dict)]
                    if top_titles:
                        fragments.append("top_articles=" + " | ".join(top_titles))

        text = "\n".join([f for f in fragments if f and f != "None"]).strip()
        if not text:
            continue

        docs.append(
            TextDocument(
                doc_id=file_path.stem,
                source="signals",
                title=f"{agent} {symbol}",
                text=text,
                symbol=symbol,
                timestamp=str(timestamp) if timestamp else None,
            )
        )

    return docs
