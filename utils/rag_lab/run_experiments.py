from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from .corpus import load_documents_from_signals
from .nlp_clustering import (
    cluster_with_agglomerative_svd,
    cluster_with_kmeans_tfidf,
    cluster_with_lda,
)
from .rag_chat import RagChatEngine


DEFAULT_QUESTIONS = [
    "Quel est le biais sur EURUSD ?",
    "Pourquoi USDJPY est en vente ?",
    "Quels risques macro influencent GBPUSD ?",
    "Quel est le sentiment dominant sur USDCHF ?",
]


def evaluate_retrieval(engine: RagChatEngine, questions: list[str]) -> dict:
    strategies = ["tfidf", "bm25", "hybrid", "semantic"]
    out = {}

    for strategy in strategies:
        top1_scores = []
        top3_hit = []
        for q in questions:
            res = engine.answer(q, strategy=strategy, top_k=5)
            contexts = res.get("contexts", [])
            if not contexts:
                top1_scores.append(0.0)
                top3_hit.append(0.0)
                continue

            # Proxy score: normalized score of best retrieved context.
            top1 = float(contexts[0].get("score", 0.0))
            top1_scores.append(top1)

            # Question mentions a pair, count hit if one of top3 contexts matches pair.
            pair_in_q = ""
            for p in ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]:
                if p in q.upper():
                    pair_in_q = p
                    break

            if not pair_in_q:
                top3_hit.append(1.0)
            else:
                matched = any(pair_in_q == str(c.get("symbol", "")).upper() for c in contexts[:3])
                top3_hit.append(1.0 if matched else 0.0)

        out[strategy] = {
            "avg_top1_score": round(mean(top1_scores) if top1_scores else 0.0, 6),
            "top3_symbol_hit_rate": round(mean(top3_hit) if top3_hit else 0.0, 6),
        }

    return out


def evaluate_clustering(documents, n_clusters: int) -> dict:
    methods = {
        "kmeans_tfidf": lambda: cluster_with_kmeans_tfidf(documents, n_clusters=n_clusters, sentiment_model="lexicon"),
        "lda_topics": lambda: cluster_with_lda(documents, n_topics=n_clusters, sentiment_model="lexicon"),
        "agglomerative_svd": lambda: cluster_with_agglomerative_svd(documents, n_clusters=n_clusters, sentiment_model="lexicon"),
    }

    out = {}
    for name, fn in methods.items():
        res = fn()
        out[name] = {
            "metrics": res.metrics,
            "topic_terms": res.topic_terms,
            "sentiment_summary": res.sentiment_summary,
        }
    return out


def main():
    parser = argparse.ArgumentParser(description="Run RAG and NLP multi-approach experiments.")
    parser.add_argument("--signals-dir", default="agents/outputs/signals", help="Path to signals json directory")
    parser.add_argument("--output", default="agents/outputs/rag_nlp_experiments.json", help="Output report path")
    parser.add_argument("--max-docs", type=int, default=300, help="Maximum number of docs loaded")
    parser.add_argument("--clusters", type=int, default=4, help="Number of clusters/topics")
    args = parser.parse_args()

    docs = load_documents_from_signals(args.signals_dir, max_docs=args.max_docs)
    if len(docs) < max(12, args.clusters * 3):
        raise RuntimeError(
            f"Not enough documents for robust clustering. docs={len(docs)} expected>={max(12, args.clusters * 3)}"
        )

    engine = RagChatEngine(docs)

    retrieval_eval = evaluate_retrieval(engine, DEFAULT_QUESTIONS)
    sample_answers = {
        strategy: [engine.answer(q, strategy=strategy, top_k=4) for q in DEFAULT_QUESTIONS]
        for strategy in ["tfidf", "bm25", "hybrid", "semantic"]
    }
    clustering_eval = evaluate_clustering(docs, n_clusters=args.clusters)

    report = {
        "dataset": {
            "num_documents": len(docs),
            "signals_dir": str(Path(args.signals_dir).resolve()),
        },
        "retrieval_experiments": retrieval_eval,
        "clustering_experiments": clustering_eval,
        "sample_chat_answers": sample_answers,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"[OK] Report written to: {out_path}")
    print(json.dumps(report["retrieval_experiments"], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
