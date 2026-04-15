"use client";

import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import styles from "./page.module.css";

export default function AgentsPage() {
    return (
        <div className={styles.pageShell}>
            <header className="flex h-14 shrink-0 items-center gap-2 border-b px-6">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Agents</h1>
            </header>

            <main className={styles.page}>
                <div className={styles.pageHd}>
                    <h1>Multi-agent architecture</h1>
                    <p>
                        Overview of specialist agents and the reporting module planned for Trady. Detailed
                        behaviors and UIs will be wired as each component is implemented.
                    </p>
                </div>

                <article className={styles.agentCard} aria-label="Transparency standards">
                    <div className={styles.agentCardHd}>
                        <span className={styles.agentNum}>T</span>
                        <div className={styles.agentTitles}>
                            <h2>Trader Transparency Standard</h2>
                            <p className={styles.subtitle}>What every decision should expose to users</p>
                        </div>
                    </div>
                    <div className={styles.agentBody}>
                        <div className={styles.trxBox}>
                            <div className={styles.trxRow}>
                                <span className={styles.trxKey}>Data provenance</span>
                                <span className={styles.trxVal}>Exact source table/feed and update timestamp</span>
                            </div>
                            <div className={styles.trxRow}>
                                <span className={styles.trxKey}>Decision basis</span>
                                <span className={styles.trxVal}>Top drivers with numeric contribution</span>
                            </div>
                            <div className={styles.trxRow}>
                                <span className={styles.trxKey}>Reliability context</span>
                                <span className={styles.trxVal}>Confidence band + fallback mode state</span>
                            </div>
                            <div className={styles.trxRow}>
                                <span className={styles.trxKey}>Freshness guard</span>
                                <span className={styles.trxVal}>Staleness warning when inputs age out</span>
                            </div>
                        </div>
                    </div>
                </article>

                <div className={styles.agentList}>
                    <article className={`${styles.agentCard} ${styles.agentCardDecision}`}>
                        <div className={`${styles.agentCardHd} ${styles.agentCardHdDecision}`}>
                            <span className={`${styles.agentNum} ${styles.agentNumDecision}`}>5</span>
                            <div className={styles.agentTitles}>
                                <h2>Agent de synthese et de decision</h2>
                                <p className={styles.subtitle}>Synthesis &amp; Decision Agent - Core Intelligence</p>
                            </div>
                        </div>
                        <div className={styles.agentBody}>
                            <div className={styles.agentSection}>
                                <strong>Role</strong>
                                Recoit les signaux et les niveaux de confiance de tous les agents specialises,
                                resout les conflits et genere une recommandation de trading finale avec un niveau
                                de confiance global.
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Contribution aux objectifs (BO)</strong>
                                <div className={styles.boTags}>
                                    <span className={styles.boTag}>BO2 - signaux actionnables</span>
                                    <span className={styles.boTag}>BO3 - reduction des faux signaux</span>
                                </div>
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Transparency Layer</strong>
                                <div className={styles.trxBox}>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Conflict resolver</span>
                                        <span className={styles.trxVal}>
                                            Show per-agent vote and final weighted decision
                                        </span>
                                    </div>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Risk disclosure</span>
                                        <span className={styles.trxVal}>
                                            Highlight disagreement and low-confidence consensus
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className={styles.agentCta}>
                                <a className={styles.agentBtn} href="/decision.html" aria-label="Open Decision Agent page">
                                    Open Decision Agent
                                </a>
                            </div>
                        </div>
                    </article>

                    <article className={styles.agentCard}>
                        <div className={styles.agentCardHd}>
                            <span className={styles.agentNum}>2</span>
                            <div className={styles.agentTitles}>
                                <h2>Agent d'analyse technique</h2>
                                <p className={styles.subtitle}>Technical Analysis Agent</p>
                            </div>
                        </div>
                        <div className={styles.agentBody}>
                            <div className={styles.agentSection}>
                                <strong>Role</strong>
                                Analyse les donnees de prix et les indicateurs techniques (RSI, MACD, moyennes
                                mobiles) pour detecter des patterns et des signaux de trading a court terme.
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Contribution aux objectifs (BO)</strong>
                                <div className={styles.boTags}>
                                    <span className={styles.boTag}>BO1 - dimension technique</span>
                                    <span className={styles.boTag}>BO2 - signaux explicables</span>
                                </div>
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Transparency Layer</strong>
                                <div className={styles.trxBox}>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Live execution view</span>
                                        <span className={styles.trxVal}>
                                            Timeframe used + candle count + model health
                                        </span>
                                    </div>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Failure transparency</span>
                                        <span className={styles.trxVal}>
                                            Show if data is insufficient or feed degraded
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className={styles.agentCta}>
                                <a className={styles.agentBtn} href="/technical.html" aria-label="Open Technical Agent page">
                                    Open Technical Agent
                                </a>
                            </div>
                        </div>
                    </article>

                    <article className={styles.agentCard}>
                        <div className={styles.agentCardHd}>
                            <span className={styles.agentNum}>3</span>
                            <div className={styles.agentTitles}>
                                <h2>Agent d'analyse macroeconomique</h2>
                                <p className={styles.subtitle}>Macroeconomic Analysis Agent</p>
                            </div>
                        </div>
                        <div className={styles.agentBody}>
                            <div className={styles.agentSection}>
                                <strong>Role</strong>
                                Interprete les indicateurs economiques (FRED) et leurs correlations avec les
                                mouvements de devises pour identifier les tendances de fond.
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Contribution aux objectifs (BO)</strong>
                                <div className={styles.boTags}>
                                    <span className={styles.boTag}>BO1 - dimension macro</span>
                                    <span className={styles.boTag}>BO2 - signaux explicables</span>
                                </div>
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Transparency Layer</strong>
                                <div className={styles.trxBox}>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Regime rationale</span>
                                        <span className={styles.trxVal}>
                                            Top macro factors with relative importance
                                        </span>
                                    </div>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Data freshness</span>
                                        <span className={styles.trxVal}>
                                            Last macro release date + staleness warning
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className={styles.agentCta}>
                                <a className={styles.agentBtn} href="/macro.html" aria-label="Open Macro Agent page">
                                    Open Macro Agent
                                </a>
                            </div>
                        </div>
                    </article>

                    <article className={styles.agentCard}>
                        <div className={styles.agentCardHd}>
                            <span className={styles.agentNum}>4</span>
                            <div className={styles.agentTitles}>
                                <h2>Agent d'analyse de sentiment</h2>
                                <p className={styles.subtitle}>Sentiment Analysis Agent</p>
                            </div>
                        </div>
                        <div className={styles.agentBody}>
                            <div className={styles.agentSection}>
                                <strong>Role</strong>
                                Traite les actualites financieres (NewsAPI) pour extraire le sentiment du marche et
                                son impact potentiel sur les devises (potentiellement via un LLM).
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Contribution aux objectifs (BO)</strong>
                                <div className={styles.boTags}>
                                    <span className={styles.boTag}>BO1 - dimension sentiment</span>
                                    <span className={styles.boTag}>BO2 - signaux explicables</span>
                                </div>
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Transparency Layer</strong>
                                <div className={styles.trxBox}>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Article traceability</span>
                                        <span className={styles.trxVal}>
                                            Source news list + hover explanation per headline
                                        </span>
                                    </div>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Inference mode</span>
                                        <span className={styles.trxVal}>
                                            Explicitly display full vs fallback inference mode
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className={styles.agentCta}>
                                <a className={styles.agentBtn} href="/sentiment.html" aria-label="Open Sentiment Agent page">
                                    Open Sentiment Agent
                                </a>
                            </div>
                        </div>
                    </article>

                    <article className={styles.agentCard}>
                        <div className={styles.agentCardHd}>
                            <span className={styles.agentNum}>6</span>
                            <div className={styles.agentTitles}>
                                <h2>Module de reporting et visualisation</h2>
                                <p className={styles.subtitle}>Reporting &amp; Visualization Module</p>
                            </div>
                        </div>
                        <div className={styles.agentBody}>
                            <div className={styles.agentSection}>
                                <strong>Role</strong>
                                Fournit des tableaux de bord en temps reel et des rapports historiques pour les
                                analystes.
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Contribution aux objectifs (BO)</strong>
                                <div className={styles.boTags}>
                                    <span className={styles.boTag}>BO5 - transparence et aide a la decision</span>
                                </div>
                            </div>
                            <div className={styles.agentSection}>
                                <strong>Transparency Layer</strong>
                                <div className={styles.trxBox}>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Audit timeline</span>
                                        <span className={styles.trxVal}>
                                            Log each recommendation with inputs and model version
                                        </span>
                                    </div>
                                    <div className={styles.trxRow}>
                                        <span className={styles.trxKey}>Post-trade review</span>
                                        <span className={styles.trxVal}>
                                            Compare predicted scenario vs realized move
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className={styles.agentCta}>
                                <a className={styles.agentBtn} href="/reporting.html" aria-label="Open Reporting dashboard">
                                    Open Reporting Dashboard
                                </a>
                                <a
                                    className={styles.agentBtn}
                                    href="/market_comparison.html"
                                    aria-label="Open Market Comparison page"
                                >
                                    Open Market Comparison
                                </a>
                                <a className={styles.agentBtn} href="/trader-guide" aria-label="Open Trader Guide page">
                                    Open Trader Guide
                                </a>
                                <a className={styles.agentBtn} href="/copilot.html" aria-label="Open AI Copilot page">
                                    Open AI Copilot
                                </a>
                            </div>
                        </div>
                    </article>
                </div>
            </main>
        </div>
    );
}
