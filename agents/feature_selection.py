"""
=====================================
FEATURE SELECTION PIPELINE
FX-AlphaLab | Major Currencies
=====================================
4 étapes de sélection :
  1. Filtrage variance (features constantes)
  2. Filtrage corrélation (multicolinéarité)
  3. Feature Importance (Random Forest)
  4. SHAP Values (explainability)

Input  : CSV générés par feature_engineering.py
Output : features sélectionnées par famille (tech/macro/sent)
         + rapport HTML + graphes
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import json

warnings.filterwarnings("ignore")
os.makedirs("outputs/feature_selection", exist_ok=True)

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

PAIRS     = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
TIMEFRAME = "1H"

# Colonnes à exclure de la sélection
EXCLUDE_COLS = ["target", "symbol", "open", "high", "low", "close", "volume"]

# Seuils
VARIANCE_THRESHOLD  = 0.01   # variance minimale
CORRELATION_CUTOFF  = 0.90   # corrélation max entre 2 features
TOP_N_FEATURES      = 20     # nb de features à garder au final

# Familles de features (préfixes)
FEATURE_FAMILIES = {
    "technical" : [
        "return_","sma_","ema_","rsi","macd","atr","bb_",
        "volatility_","volume_","doji","marubozu","bullish_candle",
        "bearish_candle","high_vol_regime","price_vs_sma50",
        "sma_cross","macd_cross"
    ],
    "macro"     : [
        "cpi","fed_funds","unemployment","yield_10y","inflation_exp",
        "gdp","real_rate","real_yield","DEXUSEU","DEXJPUS",
        "DEXUSUK","DEXSZUS"
    ],
    "sentiment" : [
        "sentiment_","news_volume","bullish_ratio","high_impact_news"
    ]
}

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def load_features(symbol: str, timeframe: str = "1H") -> pd.DataFrame:
    path = f"features/{symbol}_{timeframe}_features.csv"
    if not os.path.exists(path):
        print(f"   [WARN] File not found: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    print(f"   [OK] Loaded {symbol}: {df.shape[0]:,} rows x {df.shape[1]} cols")
    return df


def get_feature_cols(df: pd.DataFrame) -> list:
    """Retourne les colonnes de features (sans target/OHLCV)."""
    return [c for c in df.columns if c not in EXCLUDE_COLS]


def classify_feature(col: str) -> str:
    """Identifie la famille d'une feature."""
    for family, prefixes in FEATURE_FAMILIES.items():
        if any(col.startswith(p) or col == p for p in prefixes):
            return family
    return "other"


def save_plot(fig, name: str):
    path = f"outputs/feature_selection/{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved plot -> {path}")


# ─────────────────────────────────────────
# ÉTAPE 1 — FILTRAGE VARIANCE
# ─────────────────────────────────────────

def step1_variance_filter(df: pd.DataFrame, feature_cols: list) -> list:
    """
    Supprime les features quasi-constantes.
    Une feature avec variance < seuil n'apporte aucune information.
    """
    print("\nStep 1 - Variance Filter")
    X = df[feature_cols].fillna(0)

    selector = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    selector.fit(X)

    kept    = [c for c, s in zip(feature_cols, selector.get_support()) if s]
    dropped = [c for c, s in zip(feature_cols, selector.get_support()) if not s]

    print(f"   Before : {len(feature_cols)} features")
    print(f"   Dropped: {len(dropped)} low-variance features")
    print(f"   After  : {len(kept)} features")
    if dropped:
        print(f"   Removed: {dropped[:10]}{'...' if len(dropped)>10 else ''}")

    return kept


# ─────────────────────────────────────────
# ÉTAPE 2 — FILTRAGE CORRÉLATION
# ─────────────────────────────────────────

def step2_correlation_filter(df: pd.DataFrame, feature_cols: list) -> list:
    """
    Supprime les features très corrélées entre elles (multicolinéarité).
    Garde une feature par groupe corrélé (celle avec variance max).
    """
    print("\nStep 2 - Correlation Filter")
    X   = df[feature_cols].fillna(0)
    cor = X.corr().abs()

    # Matrice triangulaire supérieure
    upper = cor.where(np.triu(np.ones(cor.shape), k=1).astype(bool))

    # Features à supprimer
    to_drop = [col for col in upper.columns if any(upper[col] > CORRELATION_CUTOFF)]
    kept    = [c for c in feature_cols if c not in to_drop]

    print(f"   Before : {len(feature_cols)} features")
    print(f"   Dropped: {len(to_drop)} highly correlated features (r > {CORRELATION_CUTOFF})")
    print(f"   After  : {len(kept)} features")

    # Plot heatmap sur features gardées (max 25 pour lisibilité)
    sample_cols = kept[:25]
    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(
        df[sample_cols].corr(),
        annot=True, fmt=".2f", cmap="RdYlGn",
        center=0, linewidths=0.5, ax=ax,
        annot_kws={"size": 7}
    )
    ax.set_title("Correlation Matrix — Selected Features", fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(fontsize=8)
    save_plot(fig, "correlation_matrix")

    return kept


# ─────────────────────────────────────────
# ÉTAPE 3 — FEATURE IMPORTANCE (Random Forest)
# ─────────────────────────────────────────

def step3_rf_importance(df: pd.DataFrame, feature_cols: list, symbol: str) -> list:
    """
    Entraîne un Random Forest rapide pour estimer l'importance des features.
    Garde les TOP_N_FEATURES les plus importantes.
    """
    print(f"\nStep 3 - Random Forest Feature Importance ({symbol})")

    X = df[feature_cols].fillna(0)
    y = df["target"]

    # Split temporel (pas de shuffle sur des séries temporelles !)
    split = int(len(X) * 0.8)
    X_tr, X_te = X.iloc[:split], X.iloc[split:]
    y_tr, y_te = y.iloc[:split], y.iloc[split:]

    # Normalisation
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    # Random Forest
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=50,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_tr_s, y_tr)

    # Performance rapide
    y_pred = rf.predict(X_te_s)
    print(f"\n   Quick RF Performance ({symbol}):")
    print(classification_report(y_te, y_pred, target_names=["SELL","BUY"], digits=3))

    # Feature importances
    importances = pd.Series(rf.feature_importances_, index=feature_cols)
    importances = importances.sort_values(ascending=False)

    # Top N features
    top_features = importances.head(TOP_N_FEATURES).index.tolist()

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = []
    for f in importances.head(TOP_N_FEATURES).index:
        fam = classify_feature(f)
        colors.append({"technical": "#2196F3", "macro": "#4CAF50", "sentiment": "#FF9800"}.get(fam, "#9E9E9E"))

    importances.head(TOP_N_FEATURES).plot(kind="barh", ax=ax, color=colors[::-1])
    ax.set_xlabel("Importance (%)", fontsize=11)
    ax.set_title(f"Top {TOP_N_FEATURES} Feature Importance — {symbol}", fontsize=13, fontweight="bold")
    ax.invert_yaxis()

    # Légende familles
    from matplotlib.patches import Patch
    legend = [
        Patch(color="#2196F3", label="Technical"),
        Patch(color="#4CAF50", label="Macro"),
        Patch(color="#FF9800", label="Sentiment"),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=9)
    plt.tight_layout()
    save_plot(fig, f"feature_importance_{symbol}")

    print(f"\n   Top 10 features for {symbol}:")
    for i, (feat, imp) in enumerate(importances.head(10).items(), 1):
        fam = classify_feature(feat)
        print(f"   {i:2}. {feat:<35} {imp:.4f}  [{fam}]")

    return top_features, rf, scaler, importances


# ─────────────────────────────────────────
# ÉTAPE 4 — SHAP VALUES
# ─────────────────────────────────────────

def step4_shap_analysis(rf, X_sample: pd.DataFrame, symbol: str):
    """
    Calcule et visualise les SHAP values pour l'explainability.
    Essentiel pour justifier les décisions des agents.
    """
    print(f"\nStep 4 - SHAP Analysis ({symbol})")

    # Échantillon pour SHAP (max 500 rows pour la vitesse)
    sample = X_sample.sample(min(500, len(X_sample)), random_state=42)

    explainer   = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(sample)

    # Gestion multi-format SHAP (liste, 3D array, 2D array)
    if isinstance(shap_values, list):
        sv = shap_values[1]                        # liste de 2 classes → classe BUY
    elif shap_values.ndim == 3:
        sv = shap_values[:, :, 1]                  # shape (n, features, classes) → classe BUY
    else:
        sv = shap_values                           # déjà 2D

    # SHAP Summary Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    shap.summary_plot(
        sv, sample,
        plot_type="bar",
        show=False,
        max_display=15
    )
    plt.title(f"SHAP Feature Importance — {symbol}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    save_plot(fig, f"shap_summary_{symbol}")

    # SHAP Beeswarm (distribution des impacts)
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    shap.summary_plot(
        sv, sample,
        show=False,
        max_display=15
    )
    plt.title(f"SHAP Beeswarm — {symbol}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    save_plot(fig2, f"shap_beeswarm_{symbol}")

    # SHAP importance par feature
    shap_importance = pd.Series(
        np.abs(sv).mean(axis=0),
        index=sample.columns
    ).sort_values(ascending=False)

    print(f"   Top 10 SHAP features for {symbol}:")
    for i, (feat, val) in enumerate(shap_importance.head(10).items(), 1):
        fam = classify_feature(feat)
        print(f"   {i:2}. {feat:<35} {val:.5f}  [{fam}]")

    return shap_importance


# ─────────────────────────────────────────
# PIPELINE COMPLÈTE PAR SYMBOLE
# ─────────────────────────────────────────

def run_feature_selection(symbol: str, timeframe: str = "1H") -> dict:
    """Pipeline complète de sélection pour un symbole."""
    print(f"\n{'='*55}")
    print(f"  FEATURE SELECTION - {symbol} {timeframe}")
    print(f"{'='*55}")

    df = load_features(symbol, timeframe)
    if df.empty:
        return {}

    feature_cols = get_feature_cols(df)
    print(f"   Starting with {len(feature_cols)} features")

    # Étape 1 : variance
    cols_after_var = step1_variance_filter(df, feature_cols)

    # Étape 2 : corrélation
    cols_after_cor = step2_correlation_filter(df, cols_after_var)

    # Étape 3 : RF importance
    top_features, rf, scaler, importances = step3_rf_importance(df, cols_after_cor, symbol)

    # Étape 4 : SHAP — refit scaler sur top_features uniquement
    X_top = df[top_features].fillna(0)
    scaler_top = StandardScaler()
    X_top_s = pd.DataFrame(
        scaler_top.fit_transform(X_top),
        index=X_top.index,
        columns=X_top.columns
    )
    # Refit RF sur top features pour SHAP
    split = int(len(X_top_s) * 0.8)
    rf_top = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    rf_top.fit(X_top_s.iloc[:split], df["target"].iloc[:split])
    shap_importance = step4_shap_analysis(rf_top, X_top_s, symbol)

    # Classification par famille
    families = {f: classify_feature(f) for f in top_features}
    family_summary = pd.Series(families).value_counts().to_dict()

    result = {
        "symbol":          symbol,
        "initial_features": len(feature_cols),
        "after_variance":  len(cols_after_var),
        "after_correlation": len(cols_after_cor),
        "final_features":  top_features,
        "n_final":         len(top_features),
        "family_summary":  family_summary,
        "rf_importance":   importances.head(TOP_N_FEATURES).to_dict(),
        "shap_importance": shap_importance.head(TOP_N_FEATURES).to_dict(),
    }

    # Sauvegarde JSON
    out_path = f"outputs/feature_selection/{symbol}_selected_features.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n   Saved selection -> {out_path}")

    print(f"\n   Summary for {symbol}:")
    print(f"      Initial   : {result['initial_features']} features")
    print(f"      After var : {result['after_variance']} features")
    print(f"      After cor : {result['after_correlation']} features")
    print(f"      Final     : {result['n_final']} features")
    print(f"      Families  : {family_summary}")

    return result


# ─────────────────────────────────────────
# RAPPORT GLOBAL — TOUTES PAIRES
# ─────────────────────────────────────────

def build_global_report(all_results: dict):
    """
    Génère un rapport de synthèse :
    - Features communes à toutes les paires
    - Distribution par famille
    - Graphe comparatif
    """
    print(f"\n{'='*55}")
    print(f"  GLOBAL FEATURE SELECTION REPORT")
    print(f"{'='*55}")

    # Features communes à toutes les paires
    all_feature_sets = [set(r["final_features"]) for r in all_results.values() if r]
    if all_feature_sets:
        common_features = set.intersection(*all_feature_sets)
        print(f"\n   Common features across all pairs ({len(common_features)}):")
        for f in sorted(common_features):
            print(f"      - {f}  [{classify_feature(f)}]")

    # Graphe : nombre de features par famille par paire
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 1. Funnel de sélection
    symbols = list(all_results.keys())
    stages  = ["initial_features", "after_variance", "after_correlation", "n_final"]
    labels  = ["Initial", "After Variance", "After Correlation", "Final"]
    colors  = ["#E3F2FD", "#BBDEFB", "#64B5F6", "#1565C0"]

    x = np.arange(len(symbols))
    w = 0.2
    for i, (stage, label, color) in enumerate(zip(stages, labels, colors)):
        vals = [all_results[s].get(stage, 0) if all_results.get(s) else 0 for s in symbols]
        axes[0].bar(x + i*w, vals, w, label=label, color=color, edgecolor="white")

    axes[0].set_xticks(x + w*1.5)
    axes[0].set_xticklabels(symbols)
    axes[0].set_ylabel("Number of Features")
    axes[0].set_title("Feature Selection Funnel by Pair", fontweight="bold")
    axes[0].legend(fontsize=8)

    # 2. Distribution par famille
    family_data = {"technical": [], "macro": [], "sentiment": [], "other": []}
    for s in symbols:
        r = all_results.get(s, {})
        fs = r.get("family_summary", {})
        for fam in family_data:
            family_data[fam].append(fs.get(fam, 0))

    bottom = np.zeros(len(symbols))
    fam_colors = {"technical": "#2196F3", "macro": "#4CAF50", "sentiment": "#FF9800", "other": "#9E9E9E"}
    for fam, vals in family_data.items():
        axes[1].bar(symbols, vals, bottom=bottom, label=fam.capitalize(), color=fam_colors[fam])
        bottom += np.array(vals)

    axes[1].set_ylabel("Number of Features")
    axes[1].set_title("Final Features by Family & Pair", fontweight="bold")
    axes[1].legend(fontsize=9)

    plt.tight_layout()
    save_plot(fig, "global_feature_selection_report")

    # Sauvegarde rapport global
    global_report = {
        "common_features": list(common_features) if all_feature_sets else [],
        "per_symbol":      {s: r for s, r in all_results.items() if r}
    }
    with open("outputs/feature_selection/global_report.json", "w") as f:
        json.dump(global_report, f, indent=2, default=str)
    print("\n   Global report saved -> outputs/feature_selection/global_report.json")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  FEATURE SELECTION PIPELINE")
    print("  FX-AlphaLab | Major Currencies")
    print("=" * 55)

    all_results = {}
    for symbol in PAIRS:
        result = run_feature_selection(symbol, TIMEFRAME)
        if result:
            all_results[symbol] = result

    build_global_report(all_results)

    print(f"\n{'='*55}")
    print("  [OK] FEATURE SELECTION COMPLETE")
    print(f"  Outputs -> outputs/feature_selection/")
    print(f"{'='*55}")