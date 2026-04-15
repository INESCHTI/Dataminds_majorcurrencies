"use client";

import Link from "next/link";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import styles from "./page.module.css";

const checklistItems = [
    {
        title: "Step 1: Context",
        description: "Start from market context and volatility before signal hunting.",
    },
    {
        title: "Step 2: Consensus",
        description: "Check agent agreement and confidence quality, not confidence only.",
    },
    {
        title: "Step 3: Risk",
        description: "Define stop-loss, position size, and max loss before entry.",
    },
    {
        title: "Step 4: Review",
        description: "After execution, review outcomes and update your playbook.",
    },
];

const workflowSteps = [
    {
        index: "01",
        label: "Market scan",
        title: "Open Market Comparison page first",
        description:
            "Identify which symbols are stable vs risky. Prioritize symbols with healthier stability and acceptable disagreement.",
    },
    {
        index: "02",
        label: "Deep read",
        title: "Move to Reporting page",
        description:
            "Validate trend of drift/confidence, fallback rate, and alert transitions. Use raw event mode when you need event-level detail.",
    },
    {
        index: "03",
        label: "Entry check",
        title: "Open Decision page",
        description:
            "Confirm final signal, confidence, and risk flags. Never take a signal without reading risk flags and disagreement context.",
    },
    {
        index: "04",
        label: "Execution discipline",
        title: "Plan trade size before clicking",
        description: "Risk a small fixed percentage per trade. Example: 0.5% to 1.0% max account risk.",
    },
    {
        index: "05",
        label: "Post-trade review",
        title: "Export report and journal your decision",
        description:
            "Save PDF/CSV from Reporting and note why you entered, what invalidates setup, and what you learned.",
    },
];

const metricItems = [
    {
        title: "Disagreement (Drift)",
        description:
            "How often shadow and primary model disagree. Low is generally stable regime. Rising means changing conditions.",
    },
    {
        title: "Confidence",
        description:
            "How sure the model is. High confidence is useful only if disagreement and fallback remain controlled.",
    },
    {
        title: "Fallback Rate",
        description:
            "How often the system uses fallback mode instead of full model output. High fallback means reduced model reliability context.",
    },
    {
        title: "Alert Level",
        description:
            "Normal/Warning/Critical from disagreement thresholds. Use warning and critical as risk-management signals, not entry confirmation.",
    },
];

const bestPractices = [
    {
        title: "Use multi-page confirmation",
        description: "Start with Comparison, validate with Reporting, execute from Decision.",
    },
    {
        title: "Avoid overtrading",
        description: "Set a max number of trades/day and stop after reaching daily risk cap.",
    },
    {
        title: "Respect no-trade zones",
        description: "If confidence drops and drift rises together, stand aside.",
    },
    {
        title: "Prefer consistency over excitement",
        description: "A stable, repeatable process beats random high-risk opportunities.",
    },
];

const mistakes = [
    {
        title: "Ignoring risk flags",
        description: "Entering only because confidence looks high.",
    },
    {
        title: "Confusing confidence with certainty",
        description: "All models can be wrong in new regimes.",
    },
    {
        title: "No written plan",
        description: "Trading without predefined stop-loss and invalidation level.",
    },
    {
        title: "No review loop",
        description: "Not learning from losses/wins through reports.",
    },
];

const nextAdditions = [
    "Trade Journal page with tagged decisions and outcome review.",
    "Setup library (trend continuation, mean reversion, breakout) with checklists.",
    "Risk simulator to preview position size based on stop distance and account balance.",
];

export default function TraderGuidePage() {
    return (
        <div className={styles.pageShell}>
            <header className="flex h-14 shrink-0 items-center gap-2 border-b px-6">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Trader Guide</h1>
            </header>

            <main className={styles.page}>
                <section className={styles.hero}>
                    <h2>Beginner Trader Guide</h2>
                    <p>
                        This page is your step-by-step flow for using Trady safely and effectively. Focus on
                        process, risk discipline, and consistency. The goal is not more trades, but better decisions.
                    </p>
                    <div className={styles.heroActions}>
                        <Link href="/market-comparison" className={styles.heroBtn}>
                            Open Market Comparison
                        </Link>
                        <Link href="/reports" className={styles.heroBtn}>
                            Open Reporting
                        </Link>
                        <Link href="/agents" className={styles.heroBtn}>
                            Open Agents
                        </Link>
                    </div>
                </section>

                <section className={styles.checklist}>
                    {checklistItems.map((item) => (
                        <article key={item.title} className={styles.task}>
                            <strong>{item.title}</strong>
                            <span>{item.description}</span>
                        </article>
                    ))}
                </section>

                <section className={styles.grid}>
                    <div className={styles.column}>
                        <article className={styles.card}>
                            <div className={styles.cardHd}>Trading Workflow in Trady</div>
                            <div className={styles.cardBd}>
                                {workflowSteps.map((step) => (
                                    <div key={step.index} className={styles.step}>
                                        <div className={styles.stepIndex}>
                                            {step.index} - {step.label}
                                        </div>
                                        <div className={styles.stepTitle}>{step.title}</div>
                                        <div className={styles.stepDesc}>{step.description}</div>
                                    </div>
                                ))}
                            </div>
                        </article>

                        <article className={styles.card}>
                            <div className={styles.cardHd}>How to Read Key Metrics</div>
                            <div className={styles.cardBd}>
                                <div className={styles.list}>
                                    {metricItems.map((item) => (
                                        <div key={item.title} className={styles.listItem}>
                                            <strong>{item.title}</strong>
                                            <p>{item.description}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </article>
                    </div>

                    <div className={styles.column}>
                        <article className={styles.card}>
                            <div className={styles.cardHd}>Platform Best Practices</div>
                            <div className={styles.cardBd}>
                                <div className={styles.list}>
                                    {bestPractices.map((item) => (
                                        <div key={item.title} className={styles.listItem}>
                                            <strong>{item.title}</strong>
                                            <p>{item.description}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </article>

                        <article className={styles.card}>
                            <div className={styles.cardHd}>Common Beginner Mistakes</div>
                            <div className={styles.cardBd}>
                                <div className={styles.list}>
                                    {mistakes.map((item) => (
                                        <div key={item.title} className={styles.listItem}>
                                            <strong>{item.title}</strong>
                                            <p>
                                                <span className={styles.riskFlag}>Mistake</span>
                                                {item.description}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </article>
                    </div>
                </section>

                <section className={styles.tips}>
                    <h3>Suggested next additions</h3>
                    {nextAdditions.map((tip) => (
                        <p key={tip}>{tip}</p>
                    ))}
                </section>
            </main>
        </div>
    );
}
