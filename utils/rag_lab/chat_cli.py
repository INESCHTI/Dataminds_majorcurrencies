from __future__ import annotations

import argparse

from .corpus import load_documents_from_signals
from .rag_chat import RagChatEngine


def main():
    parser = argparse.ArgumentParser(description="Interactive RAG chat over FX signals.")
    parser.add_argument("--signals-dir", default="agents/outputs/signals")
    parser.add_argument("--strategy", choices=["tfidf", "bm25", "hybrid", "semantic"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    docs = load_documents_from_signals(args.signals_dir, max_docs=500)
    if not docs:
        raise RuntimeError("No documents found in signals directory.")

    engine = RagChatEngine(docs)
    print("[RAG CHAT] Tape une question (ou 'exit').")
    print(f"[RAG CHAT] strategy={args.strategy} top_k={args.top_k} docs={len(docs)}")

    while True:
        q = input("\nQuestion> ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit", "q"}:
            break

        res = engine.answer(q, strategy=args.strategy, top_k=args.top_k)
        print("\nReponse:")
        print(res["answer"])
        print("\nSources:")
        for c in res["contexts"]:
            print(f"- {c['doc_id']} | {c['symbol']} | score={c['score']}")


if __name__ == "__main__":
    main()
