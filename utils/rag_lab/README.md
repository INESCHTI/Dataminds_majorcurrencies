# RAG + NLP Multi-Approach Lab

Ce module ajoute 3 capacites:

1. Chat base sur RAG pour repondre aux questions.
2. Clustering NLP pour identifier topics/sentiment.
3. Evaluation comparee de plusieurs approches (retrieval + clustering), avec scores quantifies.

## Approches testees

### Retrieval RAG
- `tfidf`: similarite cosinus TF-IDF.
- `bm25`: retrieval lexical BM25.
- `hybrid`: fusion RRF (Reciprocal Rank Fusion) entre TF-IDF et BM25.
- `semantic`: embeddings sentence-transformers + similarite cosinus.

## Approche 2 (semantic) - explication claire

`semantic` transforme chaque document et la question en vecteurs numeriques (embeddings).
Ensuite, on calcule la similarite cosinus entre la question et tous les documents.

Pourquoi c'est utile:
- robuste aux reformulations (mots differents, meme sens),
- meilleure recuperation quand la question n'utilise pas les memes mots que les documents,
- souvent plus stable sur des questions metier (macro/sentiment) formulees en langage naturel.

Limites:
- plus couteux en calcul que BM25/TF-IDF,
- necessite le package `sentence-transformers` et un modele local,
- peut etre moins interpretable qu'un matching lexical pur.

Quand l'utiliser:
- questions conversationnelles, longues, ou paraphrasees,
- recherche de contexte "par sens" et non par mot exact.

Fallback:
- si le modele embeddings n'est pas disponible, la strategie `semantic` retombe automatiquement sur `tfidf`.

### Clustering NLP
- `kmeans_tfidf`
- `lda_topics`
- `agglomerative_svd`

### Sentiment quantifie
- Score positif
- Score negatif
- Score compound
- Resume sentiment par cluster

## Execution

Depuis la racine du projet:

```bash
python -m utils.rag_lab.run_experiments --signals-dir agents/outputs/signals --output agents/outputs/rag_nlp_experiments.json --clusters 4
```

Chat interactif:

```bash
python -m utils.rag_lab.chat_cli --signals-dir agents/outputs/signals --strategy semantic --top-k 4
```

## API interne Next.js (sans FastAPI)

Routes disponibles dans le frontend:
- `POST /api/v2/rag/chat`
- `GET /api/v2/rag/benchmark`

Exemple chat:

```json
{
	"question": "Pourquoi USDJPY est en vente ?",
	"strategy": "semantic",
	"top_k": 4,
	"max_docs": 400
}
```

Exemple benchmark:

`/api/v2/rag/benchmark?clusters=4&max_docs=300`

Le rapport JSON contient:
- performance de retrieval par strategie,
- qualite de clustering (`silhouette`, `davies_bouldin`),
- topics par cluster,
- quantification sentiment par cluster,
- exemples de reponses chat pour chaque strategie.

## Fichiers
- `utils/rag_lab/corpus.py`: chargement du corpus depuis les signaux.
- `utils/rag_lab/rag_chat.py`: moteur RAG multi-strategies.
- `utils/rag_lab/nlp_clustering.py`: clustering + scoring sentiment.
- `utils/rag_lab/run_experiments.py`: benchmark compare multi-approches.
