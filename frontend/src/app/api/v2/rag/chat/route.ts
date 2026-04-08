import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { spawn } from "child_process";

export const runtime = "nodejs";

type ChatBody = {
    question?: string;
    strategy?: "tfidf" | "bm25" | "hybrid" | "semantic";
    top_k?: number;
    max_docs?: number;
};

function runPython(args: string[], cwd: string): Promise<{ stdout: string; stderr: string; code: number | null }> {
    return new Promise((resolve) => {
        const py = process.env.PYTHON_EXECUTABLE || "python";
        const child = spawn(py, args, { cwd, shell: false });

        let stdout = "";
        let stderr = "";

        child.stdout.on("data", (d) => {
            stdout += d.toString();
        });

        child.stderr.on("data", (d) => {
            stderr += d.toString();
        });

        child.on("close", (code) => {
            resolve({ stdout, stderr, code });
        });

        child.on("error", (err) => {
            resolve({ stdout, stderr: `${stderr}\n${String(err)}`, code: -1 });
        });
    });
}

export async function POST(request: NextRequest) {
    const body = (await request.json().catch(() => ({}))) as ChatBody;
    const question = String(body?.question || "").trim();

    if (!question) {
        return NextResponse.json({ error: "question is required" }, { status: 400 });
    }

    const strategy = String(body?.strategy || "hybrid").toLowerCase();
    if (!["tfidf", "bm25", "hybrid", "semantic"].includes(strategy)) {
        return NextResponse.json({ error: "invalid strategy" }, { status: 400 });
    }

    const topK = Number.isFinite(Number(body?.top_k)) ? Number(body?.top_k) : 5;
    const maxDocs = Number.isFinite(Number(body?.max_docs)) ? Number(body?.max_docs) : 500;

    const repoRoot = path.resolve(process.cwd(), "..");
    const signalsDir = path.resolve(repoRoot, "agents", "outputs", "signals");

    const commandArgs = [
        "-m",
        "utils.rag_lab.chat_once",
        "--signals-dir",
        signalsDir,
        "--question",
        question,
        "--strategy",
        strategy,
        "--top-k",
        String(topK),
        "--max-docs",
        String(maxDocs),
    ];

    const started = Date.now();
    const run = await runPython(commandArgs, repoRoot);
    const elapsed = Date.now() - started;

    if (run.code !== 0 && !run.stdout.trim()) {
        return NextResponse.json(
            { error: "rag_chat_failed", stderr: run.stderr.trim(), execution_time_ms: elapsed },
            { status: 500 }
        );
    }

    try {
        const payload = JSON.parse(run.stdout.trim());
        return NextResponse.json({ ...payload, execution_time_ms: elapsed });
    } catch {
        return NextResponse.json(
            {
                error: "rag_chat_invalid_output",
                stdout: run.stdout.trim(),
                stderr: run.stderr.trim(),
                execution_time_ms: elapsed,
            },
            { status: 500 }
        );
    }
}
