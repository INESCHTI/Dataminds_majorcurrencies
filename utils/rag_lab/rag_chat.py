from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .corpus import TextDocument

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

RetrievalStrategy = Literal["tfidf", "bm25", "hybrid", "semantic"]


@dataclass
class RetrievedChunk:
    doc_id: str
    score: float
    title: str
    text: str
    symbol: str


class BM25Retriever:
    def __init__(self, docs: list[TextDocument]):
        self.docs = docs
        self.tokens = [self._tokenize(d.text) for d in docs]
        self.doc_len = np.array([len(t) for t in self.tokens], dtype=float)
        self.avg_dl = float(np.mean(self.doc_len)) if len(self.doc_len) else 0.0
        self.k1 = 1.5
        self.b = 0.75

        self.df = {}
        for tokens in self.tokens:
            seen = set(tokens)
            for t in seen:
                self.df[t] = self.df.get(t, 0) + 1

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z]{2,}", text.lower())

    def _idf(self, term: str) -> float:
        n_docs = max(1, len(self.docs))
        df = self.df.get(term, 0)
        return math.log(1 + (n_docs - df + 0.5) / (df + 0.5))

    def score(self, query: str) -> np.ndarray:
        if not self.docs:
            return np.array([])
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return np.zeros(len(self.docs), dtype=float)

        out = np.zeros(len(self.docs), dtype=float)
        for i, tokens in enumerate(self.tokens):
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            dl = self.doc_len[i] if i < len(self.doc_len) else 0.0

            score = 0.0
            for term in q_tokens:
                if term not in tf:
                    continue
                freq = tf[term]
                idf = self._idf(term)
                den = freq + self.k1 * (1 - self.b + self.b * (dl / (self.avg_dl + 1e-9)))
                score += idf * (freq * (self.k1 + 1)) / (den + 1e-9)

            out[i] = score

        return out


class RagChatEngine:
    def __init__(self, documents: list[TextDocument]):
        self.documents = documents
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=15000)
        self.doc_matrix = self.vectorizer.fit_transform([d.text for d in documents]) if documents else None
        self.bm25 = BM25Retriever(documents)
        self.semantic_model = None
        self.semantic_embeddings = None

        if SENTENCE_TRANSFORMERS_AVAILABLE and documents:
            try:
                self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
                texts = [d.text for d in documents]
                self.semantic_embeddings = self.semantic_model.encode(texts, normalize_embeddings=True)
            except Exception:
                self.semantic_model = None
                self.semantic_embeddings = None

    def retrieve(self, question: str, top_k: int = 5, strategy: RetrievalStrategy = "hybrid") -> list[RetrievedChunk]:
        if not self.documents:
            return []

        tfidf_scores = np.zeros(len(self.documents), dtype=float)
        bm25_scores = np.zeros(len(self.documents), dtype=float)
        semantic_scores = np.zeros(len(self.documents), dtype=float)

        if self.doc_matrix is not None:
            q = self.vectorizer.transform([question])
            tfidf_scores = (self.doc_matrix @ q.T).toarray().reshape(-1)

        bm25_scores = self.bm25.score(question)

        if self.semantic_model is not None and self.semantic_embeddings is not None:
            try:
                q_vec = self.semantic_model.encode([question], normalize_embeddings=True)
                semantic_scores = cosine_similarity(q_vec, self.semantic_embeddings).reshape(-1)
            except Exception:
                semantic_scores = np.zeros(len(self.documents), dtype=float)

        if strategy == "tfidf":
            final = tfidf_scores
        elif strategy == "bm25":
            final = bm25_scores
        elif strategy == "semantic":
            # Fallback if embeddings are unavailable.
            if self.semantic_model is None or self.semantic_embeddings is None:
                final = tfidf_scores
            else:
                final = semantic_scores
        else:
            final = self._hybrid_rrf(tfidf_scores, bm25_scores)

        idx = np.argsort(final)[::-1][:top_k]
        return [
            RetrievedChunk(
                doc_id=self.documents[i].doc_id,
                score=float(final[i]),
                title=self.documents[i].title,
                text=self.documents[i].text,
                symbol=self.documents[i].symbol,
            )
            for i in idx
        ]

    @staticmethod
    def _hybrid_rrf(scores_a: np.ndarray, scores_b: np.ndarray, k: int = 60) -> np.ndarray:
        if len(scores_a) == 0:
            return scores_a
        rank_a = np.argsort(np.argsort(-scores_a))
        rank_b = np.argsort(np.argsort(-scores_b))
        return 1.0 / (k + rank_a + 1) + 1.0 / (k + rank_b + 1)

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        bits = re.split(r"(?<=[.!?])\s+", text.strip())
        return [b.strip() for b in bits if b.strip()]

    @staticmethod
    def _keyword_overlap_score(sentence: str, query: str) -> float:
        q_tokens = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
        s_tokens = set(re.findall(r"[a-zA-Z]{3,}", sentence.lower()))
        if not q_tokens:
            return 0.0
        return len(q_tokens & s_tokens) / len(q_tokens)

    def answer(self, question: str, strategy: RetrievalStrategy = "hybrid", top_k: int = 5) -> dict:
        chunks = self.retrieve(question, strategy=strategy, top_k=top_k)
        if not chunks:
            return {
                "question": question,
                "strategy": strategy,
                "answer": "Je n'ai pas trouve de contexte pertinent.",
                "contexts": [],
            }

        candidate_sentences: list[tuple[float, str, RetrievedChunk]] = []
        for chunk in chunks:
            for sentence in self._split_sentences(chunk.text):
                score = self._keyword_overlap_score(sentence, question)
                candidate_sentences.append((score + chunk.score * 0.1, sentence, chunk))

        candidate_sentences.sort(key=lambda x: x[0], reverse=True)
        best = candidate_sentences[:3] if candidate_sentences else []

        if best:
            answer = " ".join([s for _, s, _ in best])
        else:
            answer = chunks[0].text[:400]

        contexts = [
            {
                "doc_id": c.doc_id,
                "title": c.title,
                "symbol": c.symbol,
                "score": round(c.score, 6),
            }
            for c in chunks
        ]

        return {
            "question": question,
            "strategy": strategy,
            "answer": answer,
            "contexts": contexts,
        }
