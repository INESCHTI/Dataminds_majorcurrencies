from __future__ import annotations

import argparse
import json

from .corpus import load_documents_from_signals
from .rag_chat import RagChatEngine


def main():
    parser = argparse.ArgumentParser(description="One-shot RAG chat query.")
    parser.add_argument("--signals-dir", default="agents/outputs/signals")
    parser.add_argument("--question", required=True)
    parser.add_argument("--strategy", choices=["tfidf", "bm25", "hybrid", "semantic"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-docs", type=int, default=500)
    args = parser.parse_args()

    docs = load_documents_from_signals(args.signals_dir, max_docs=args.max_docs)
    if not docs:
        print(json.dumps({"success": False, "error": "no_documents"}, ensure_ascii=True))
        return

    engine = RagChatEngine(docs)
    result = engine.answer(args.question, strategy=args.strategy, top_k=args.top_k)

    payload = {
        "success": True,
        "strategy": args.strategy,
        "documents_indexed": len(docs),
        "result": result,
    }
    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
