from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics import davies_bouldin_score, silhouette_score

from .corpus import TextDocument

try:
    from nltk.sentiment import SentimentIntensityAnalyzer

    VADER_AVAILABLE = True
except Exception:
    VADER_AVAILABLE = False


@dataclass
class ClusterResult:
    method: str
    labels: list[int]
    topic_terms: dict[int, list[str]]
    sentiment_summary: dict[int, dict[str, float]]
    metrics: dict[str, float]


LEXICON_POS = {
    "buy", "bullish", "strong", "rise", "rally", "gain", "positive", "upside", "growth", "beat", "hawkish"
}
LEXICON_NEG = {
    "sell", "bearish", "weak", "drop", "decline", "negative", "downside", "loss", "miss", "dovish", "risk"
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]{3,}", text.lower())


def lexicon_sentiment(text: str) -> dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {"positive": 0.0, "negative": 0.0, "compound": 0.0}
    pos = sum(1 for t in tokens if t in LEXICON_POS)
    neg = sum(1 for t in tokens if t in LEXICON_NEG)
    total = max(1, pos + neg)
    compound = (pos - neg) / total
    return {
        "positive": pos / max(1, len(tokens)),
        "negative": neg / max(1, len(tokens)),
        "compound": compound,
    }


def vader_sentiment(text: str) -> dict[str, float]:
    if not VADER_AVAILABLE:
        return lexicon_sentiment(text)
    try:
        sia = SentimentIntensityAnalyzer()
        raw = sia.polarity_scores(text)
        return {
            "positive": float(raw.get("pos", 0.0)),
            "negative": float(raw.get("neg", 0.0)),
            "compound": float(raw.get("compound", 0.0)),
        }
    except Exception:
        return lexicon_sentiment(text)


def _extract_topic_terms_from_centroids(vectorizer: TfidfVectorizer, centroids: np.ndarray, top_n: int = 8) -> dict[int, list[str]]:
    terms = np.array(vectorizer.get_feature_names_out())
    out: dict[int, list[str]] = {}
    for i, row in enumerate(centroids):
        idx = np.argsort(row)[::-1][:top_n]
        out[i] = terms[idx].tolist()
    return out


def _cluster_sentiment_summary(labels: np.ndarray, scores: list[dict[str, float]]) -> dict[int, dict[str, float]]:
    summary: dict[int, dict[str, float]] = {}
    for cluster in sorted(set(labels.tolist())):
        rows = [scores[i] for i in range(len(scores)) if int(labels[i]) == int(cluster)]
        if not rows:
            summary[int(cluster)] = {"avg_positive": 0.0, "avg_negative": 0.0, "avg_compound": 0.0, "size": 0}
            continue
        summary[int(cluster)] = {
            "avg_positive": float(np.mean([r["positive"] for r in rows])),
            "avg_negative": float(np.mean([r["negative"] for r in rows])),
            "avg_compound": float(np.mean([r["compound"] for r in rows])),
            "size": len(rows),
        }
    return summary


def _quality_metrics(features: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    unique = len(set(labels.tolist()))
    if unique < 2:
        return {"silhouette": -1.0, "davies_bouldin": 999.0}
    return {
        "silhouette": float(silhouette_score(features, labels)),
        "davies_bouldin": float(davies_bouldin_score(features, labels)),
    }


def cluster_with_kmeans_tfidf(documents: list[TextDocument], n_clusters: int = 4, sentiment_model: str = "lexicon") -> ClusterResult:
    texts = [d.text for d in documents]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
    X = vectorizer.fit_transform(texts)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = km.fit_predict(X)

    scorer = vader_sentiment if sentiment_model == "vader" else lexicon_sentiment
    sentiment_scores = [scorer(t) for t in texts]

    return ClusterResult(
        method="kmeans_tfidf",
        labels=labels.tolist(),
        topic_terms=_extract_topic_terms_from_centroids(vectorizer, km.cluster_centers_),
        sentiment_summary=_cluster_sentiment_summary(labels, sentiment_scores),
        metrics=_quality_metrics(X.toarray(), labels),
    )


def cluster_with_lda(documents: list[TextDocument], n_topics: int = 4, sentiment_model: str = "lexicon") -> ClusterResult:
    texts = [d.text for d in documents]
    vectorizer = CountVectorizer(stop_words="english", max_features=10000)
    X = vectorizer.fit_transform(texts)

    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42, learning_method="batch")
    topic_distribution = lda.fit_transform(X)
    labels = np.argmax(topic_distribution, axis=1)

    terms = np.array(vectorizer.get_feature_names_out())
    topic_terms: dict[int, list[str]] = {}
    for i, weights in enumerate(lda.components_):
        idx = np.argsort(weights)[::-1][:8]
        topic_terms[i] = terms[idx].tolist()

    scorer = vader_sentiment if sentiment_model == "vader" else lexicon_sentiment
    sentiment_scores = [scorer(t) for t in texts]

    return ClusterResult(
        method="lda_topics",
        labels=labels.tolist(),
        topic_terms=topic_terms,
        sentiment_summary=_cluster_sentiment_summary(labels, sentiment_scores),
        metrics=_quality_metrics(topic_distribution, labels),
    )


def cluster_with_agglomerative_svd(documents: list[TextDocument], n_clusters: int = 4, sentiment_model: str = "lexicon") -> ClusterResult:
    texts = [d.text for d in documents]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=12000)
    X = vectorizer.fit_transform(texts)

    svd = TruncatedSVD(n_components=min(64, max(2, X.shape[1] - 1)), random_state=42)
    Z = svd.fit_transform(X)

    model = AgglomerativeClustering(n_clusters=n_clusters)
    labels = model.fit_predict(Z)

    # Approximate topic terms by mean tf-idf per cluster.
    terms = np.array(vectorizer.get_feature_names_out())
    dense = X.toarray()
    topic_terms: dict[int, list[str]] = {}
    for cluster in sorted(set(labels.tolist())):
        idx = np.where(labels == cluster)[0]
        center = dense[idx].mean(axis=0)
        top_idx = np.argsort(center)[::-1][:8]
        topic_terms[int(cluster)] = terms[top_idx].tolist()

    scorer = vader_sentiment if sentiment_model == "vader" else lexicon_sentiment
    sentiment_scores = [scorer(t) for t in texts]

    return ClusterResult(
        method="agglomerative_svd",
        labels=labels.tolist(),
        topic_terms=topic_terms,
        sentiment_summary=_cluster_sentiment_summary(labels, sentiment_scores),
        metrics=_quality_metrics(Z, labels),
    )
