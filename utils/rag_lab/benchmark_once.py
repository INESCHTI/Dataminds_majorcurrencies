from __future__ import annotations

import argparse
import json

from .corpus import load_documents_from_signals
from .rag_chat import RagChatEngine
from .run_experiments import DEFAULT_QUESTIONS, evaluate_clustering, evaluate_retrieval


def main():
    parser = argparse.ArgumentParser(description="One-shot RAG benchmark JSON output.")
    parser.add_argument("--signals-dir", default="agents/outputs/signals")
    parser.add_argument("--clusters", type=int, default=4)
    parser.add_argument("--max-docs", type=int, default=300)
    args = parser.parse_args()

    docs = load_documents_from_signals(args.signals_dir, max_docs=args.max_docs)
    if len(docs) < max(12, args.clusters * 3):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "not_enough_documents",
                    "documents": len(docs),
                    "required": max(12, args.clusters * 3),
                },
                ensure_ascii=True,
            )
        )
        return

    engine = RagChatEngine(docs)
    retrieval = evaluate_retrieval(engine, DEFAULT_QUESTIONS)
    clustering = evaluate_clustering(docs, n_clusters=args.clusters)

    payload = {
        "success": True,
        "documents": len(docs),
        "retrieval_experiments": retrieval,
        "clustering_experiments": clustering,
    }
    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
