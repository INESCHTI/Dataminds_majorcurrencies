"""
NLP utilities for the Sentiment Agent.

Provides cached model handles for:
- FinBERT sentiment probabilities
- Lightweight sentence embeddings
- NER extraction with transformer model (fallback regex rules)
"""
from __future__ import annotations

import hashlib
import logging
import re
import threading
from functools import lru_cache
from typing import Dict, List, Tuple

import numpy as np

LOGGER = logging.getLogger("FXAlphaLab.SentimentNLP")

FINBERT_MODEL = "ProsusAI/finbert"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
NER_MODEL = "dslim/bert-base-NER"

CURRENCY_CODES = {"USD", "EUR", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD", "CNY"}
CENTRAL_BANK_KEYWORDS = {
    "FED": "Federal Reserve",
    "FOMC": "Federal Reserve",
    "ECB": "European Central Bank",
    "BOE": "Bank of England",
    "BOJ": "Bank of Japan",
    "SNB": "Swiss National Bank",
}
COUNTRY_KEYWORDS = {
    "UNITED STATES": "United States",
    "EUROZONE": "Eurozone",
    "UNITED KINGDOM": "United Kingdom",
    "JAPAN": "Japan",
    "SWITZERLAND": "Switzerland",
}

PAIR_TO_CURRENCIES = {
    "EURUSD": {"EUR", "USD"},
    "USDJPY": {"USD", "JPY"},
    "GBPUSD": {"GBP", "USD"},
    "USDCHF": {"USD", "CHF"},
}


def _safe_import_transformers():
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

        return AutoTokenizer, AutoModelForSequenceClassification, pipeline
    except Exception as e:
        LOGGER.warning("transformers unavailable, using NLP fallbacks: %s", e)
        return None, None, None


def _safe_import_sentence_transformers():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer
    except Exception as e:
        LOGGER.warning("sentence-transformers unavailable, using embedding fallback: %s", e)
        return None


_model_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_finbert_pipeline():
    AutoTokenizer, AutoModelForSequenceClassification, pipeline = _safe_import_transformers()
    if pipeline is None:
        return None

    with _model_lock:
        tok = AutoTokenizer.from_pretrained(FINBERT_MODEL)
        mdl = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
        clf = pipeline("text-classification", model=mdl, tokenizer=tok, return_all_scores=True)
    return clf


@lru_cache(maxsize=1)
def get_ner_pipeline():
    AutoTokenizer, _, pipeline = _safe_import_transformers()
    if pipeline is None:
        return None

    with _model_lock:
        tok = AutoTokenizer.from_pretrained(NER_MODEL)
        ner = pipeline("ner", model=NER_MODEL, tokenizer=tok, aggregation_strategy="simple")
    return ner


@lru_cache(maxsize=1)
def get_embedding_model():
    SentenceTransformer = _safe_import_sentence_transformers()
    if SentenceTransformer is None:
        return None

    with _model_lock:
        emb_model = SentenceTransformer(EMBED_MODEL)
    return emb_model


def sentiment_probs(text: str) -> Dict[str, float]:
    text = (text or "").strip()
    if not text:
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "score": 0.0}

    clf = get_finbert_pipeline()
    if clf is None:
        lower = text.lower()
        pos_words = ("rise", "gain", "rally", "strong", "bullish", "hawkish")
        neg_words = ("fall", "drop", "weak", "bearish", "dovish", "recession")
        pos = float(sum(w in lower for w in pos_words))
        neg = float(sum(w in lower for w in neg_words))
        total = max(1.0, pos + neg + 1.0)
        p_pos = pos / total
        p_neg = neg / total
        p_neu = max(0.0, 1.0 - (p_pos + p_neg))
    else:
        raw = clf(text[:2000])
        preds = raw
        if isinstance(raw, list) and raw and isinstance(raw[0], list):
            preds = raw[0]

        if isinstance(preds, dict):
            preds = [preds]
        if not isinstance(preds, list):
            preds = []

        out = {}
        for p in preds:
            if not isinstance(p, dict):
                continue
            lbl = str(p.get("label", "")).lower()
            scr = float(p.get("score", 0.0) or 0.0)
            if lbl:
                out[lbl] = scr
        p_pos = out.get("positive", 0.0)
        p_neg = out.get("negative", 0.0)
        p_neu = out.get("neutral", 0.0)

    score = float(np.clip(p_pos - p_neg, -1.0, 1.0))
    return {
        "positive": p_pos,
        "negative": p_neg,
        "neutral": p_neu,
        "score": score,
    }


def text_embedding(text: str) -> np.ndarray:
    text = (text or "").strip()
    if not text:
        return np.zeros(384, dtype=np.float32)

    emb_model = get_embedding_model()
    if emb_model is None:
        # Stable deterministic fallback vector from text hash.
        h = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
        arr = np.frombuffer(h * 12, dtype=np.uint8)[:384].astype(np.float32)
        arr = (arr - arr.mean()) / (arr.std() + 1e-6)
        return arr

    vec = emb_model.encode([text[:3000]], normalize_embeddings=True)
    return np.asarray(vec[0], dtype=np.float32)


def embedding_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _regex_entities(text: str) -> Dict[str, List[str]]:
    upper = (text or "").upper()

    currencies = sorted({c for c in CURRENCY_CODES if re.search(rf"\b{c}\b", upper)})

    central_banks = []
    for key, label in CENTRAL_BANK_KEYWORDS.items():
        if key in upper:
            central_banks.append(label)

    countries = []
    for key, label in COUNTRY_KEYWORDS.items():
        if key in upper:
            countries.append(label)

    return {
        "currencies": sorted(set(currencies)),
        "central_banks": sorted(set(central_banks)),
        "countries": sorted(set(countries)),
        "companies": [],
    }


def extract_entities(text: str) -> Dict[str, List[str]]:
    base = _regex_entities(text)

    ner = get_ner_pipeline()
    if ner is None:
        return base

    try:
        records = ner((text or "")[:2000])
    except Exception:
        return base

    companies = set(base.get("companies", []))
    for r in records:
        entity_group = str(r.get("entity_group", "")).upper()
        word = str(r.get("word", "")).strip()
        if not word:
            continue
        if entity_group == "ORG" and len(word) > 2:
            companies.add(word)

    base["companies"] = sorted(companies)
    return base


def map_entities_to_assets(entities: Dict[str, List[str]]) -> List[str]:
    cset = set(entities.get("currencies", []))
    assets: List[str] = []
    for pair, pair_ccy in PAIR_TO_CURRENCIES.items():
        if pair_ccy.issubset(cset):
            assets.append(pair)

    # If one side appears, include common USD pairs as weakly affected assets.
    if "USD" in cset and not assets:
        assets.extend(["EURUSD", "USDJPY", "GBPUSD", "USDCHF"])

    return sorted(set(assets))


def get_nlp_signal(text: str) -> Dict:
    probs = sentiment_probs(text)
    entities = extract_entities(text)
    assets = map_entities_to_assets(entities)
    emb = text_embedding(text)

    return {
        "sentiment_positive": probs["positive"],
        "sentiment_negative": probs["negative"],
        "sentiment_neutral": probs["neutral"],
        "sentiment_score": probs["score"],
        "entities": entities,
        "assets": assets,
        "embedding": emb,
    }
