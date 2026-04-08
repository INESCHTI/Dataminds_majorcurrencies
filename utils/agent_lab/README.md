# Agent Lab - LLM + Tools + Scripts + APIs

Objectif: montrer qu'un LLM seul ne suffit pas, et qu'il doit orchestrer des outils.

## Ce module fait quoi

1. Le "cerveau" choisit quels outils appeler selon la question.
2. Il execute automatiquement scripts/APIs necessaires.
3. Il combine sentiment + analyse technique pour prendre une decision.
4. Il compare plusieurs methodes:
- `rule_based`
- `nlp_router`
- `llm_langchain_router` (avec fallback si LLM indisponible)

## Outils disponibles

- `technical_snapshot`: snapshot technique (API puis fallback fichiers signaux)
- `sentiment_snapshot`: dernier signal sentiment
- `freshness_health`: etat de fraicheur des donnees via API
- `fuse_sentiment_technical`: fusion des deux analyses

## Pourquoi c'est important

Un LLM sans tools peut "parler" mais pas agir.
Ici, la decision est fondee sur des donnees recuperees en temps reel/fichiers,
pas uniquement sur du texte generique.

## Execution benchmark multi-methodes

```bash
python -m utils.agent_lab.run_methods_benchmark --api-base http://localhost:3000 --output agents/outputs/agent_tool_methods_report.json
```

Le rapport contient:
- succes par methode,
- latence moyenne,
- nombre moyen d'outils appeles,
- score moyen de fusion sentiment+technique,
- traces detaillees question par question.

## Interpretation claire

- `rule_based`: rapide, explicable, mais limite sur requetes complexes.
- `nlp_router`: meilleure generalisation des intentions (NLP supervise simple).
- `llm_langchain_router`: plus flexible pour planifier les outils, mais depend du modele local/API.

Recommandation pratique:
- Production robuste: `nlp_router` + garde-fous `rule_based`.
- Exploration avancee: `llm_langchain_router` pour planning adaptatif.
