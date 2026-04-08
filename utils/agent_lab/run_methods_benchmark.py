from __future__ import annotations

import argparse
import json
from statistics import mean

from .methods import run_llm_langchain_router, run_nlp_router, run_rule_based


QUESTIONS = [
    "Combiner sentiment et analyse technique pour EURUSD",
    "Quel est le sentiment news sur GBPUSD ?",
    "Donne un signal technique pour USDJPY",
    "Verifier la fraicheur et la latence des donnees puis decider sur USDCHF",
]


def evaluate_runs(runs: list[dict]) -> dict:
    if not runs:
        return {
            "success_rate": 0.0,
            "avg_duration_ms": 0.0,
            "avg_tools_called": 0.0,
            "avg_abs_fusion_score": 0.0,
        }

    success = []
    durations = []
    tools_count = []
    fusion_abs = []

    for r in runs:
        outputs = r.get("tool_outputs", [])
        ok = any(bool(o.get("ok")) for o in outputs)
        success.append(1.0 if ok else 0.0)
        durations.append(float(r.get("duration_ms", 0)))
        tools_count.append(float(len(r.get("selected_tools", []))))
        fusion_abs.append(abs(float(r.get("final_decision", {}).get("fusion_score", 0.0) or 0.0)))

    return {
        "success_rate": round(mean(success), 4),
        "avg_duration_ms": round(mean(durations), 2),
        "avg_tools_called": round(mean(tools_count), 2),
        "avg_abs_fusion_score": round(mean(fusion_abs), 4),
    }


def run_all(api_base: str, llm_model: str) -> dict:
    methods = {
        "rule_based": lambda q: run_rule_based(q, api_base=api_base),
        "nlp_router": lambda q: run_nlp_router(q, api_base=api_base),
        "llm_langchain_router": lambda q: run_llm_langchain_router(q, api_base=api_base, model=llm_model),
    }

    report = {
        "questions": QUESTIONS,
        "per_method_runs": {},
        "summary": {},
    }

    for name, fn in methods.items():
        runs = []
        for q in QUESTIONS:
            run = fn(q)
            runs.append(
                {
                    "method": run.method,
                    "question": run.question,
                    "pair": run.pair,
                    "selected_tools": run.selected_tools,
                    "tool_outputs": run.tool_outputs,
                    "final_decision": run.final_decision,
                    "duration_ms": run.duration_ms,
                }
            )
        report["per_method_runs"][name] = runs
        report["summary"][name] = evaluate_runs(runs)

    return report


def main():
    parser = argparse.ArgumentParser(description="Compare multiple agent methods (LLM, NLP, rules) with tools/scripts/API calls.")
    parser.add_argument("--api-base", default="http://localhost:3000")
    parser.add_argument("--llm-model", default="qwen2.5")
    parser.add_argument("--output", default="agents/outputs/agent_tool_methods_report.json")
    args = parser.parse_args()

    report = run_all(api_base=args.api_base, llm_model=args.llm_model)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=True)

    print(f"[OK] report: {args.output}")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
