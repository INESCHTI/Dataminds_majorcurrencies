import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { spawn } from "child_process";

export const runtime = "nodejs";

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

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const clusters = Number(searchParams.get("clusters") || 4);
    const maxDocs = Number(searchParams.get("max_docs") || 300);

    const repoRoot = path.resolve(process.cwd(), "..");
    const signalsDir = path.resolve(repoRoot, "agents", "outputs", "signals");

    const args = [
        "-m",
        "utils.rag_lab.benchmark_once",
        "--signals-dir",
        signalsDir,
        "--clusters",
        String(Number.isFinite(clusters) ? clusters : 4),
        "--max-docs",
        String(Number.isFinite(maxDocs) ? maxDocs : 300),
    ];

    const started = Date.now();
    const run = await runPython(args, repoRoot);
    const elapsed = Date.now() - started;

    if (run.code !== 0 && !run.stdout.trim()) {
        return NextResponse.json(
            { error: "rag_benchmark_failed", stderr: run.stderr.trim(), execution_time_ms: elapsed },
            { status: 500 }
        );
    }

    try {
        const payload = JSON.parse(run.stdout.trim());
        return NextResponse.json({ ...payload, execution_time_ms: elapsed });
    } catch {
        return NextResponse.json(
            {
                error: "rag_benchmark_invalid_output",
                stdout: run.stdout.trim(),
                stderr: run.stderr.trim(),
                execution_time_ms: elapsed,
            },
            { status: 500 }
        );
    }
}
