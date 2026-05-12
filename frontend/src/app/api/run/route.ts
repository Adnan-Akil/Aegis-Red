import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export async function POST(req: Request) {
  try {
    const { url, headless, mutations, iterations, user_id } = await req.json();

    // 1. Security Validation: Ensure URL is an actual URL or a safe predefined target name
    const safeTargets = ["chatbot", "rag", "tool_agent", "hardened_bot", "hardened_rag", "hardened_tool"];
    const isValidUrl = url.startsWith("http://") || url.startsWith("https://");
    const isSafeTarget = safeTargets.includes(url);

    if (!isValidUrl && !isSafeTarget) {
      return NextResponse.json({ 
        success: false, 
        error: "Invalid target. Must be a valid URL (http/https) or a predefined local target name." 
      }, { status: 400 });
    }

    // The Python project is in the parent directory of frontend
    const rootDir = path.join(process.cwd(), "..");
    const pythonExecutable = path.join(rootDir, "venv", "Scripts", "python.exe");

    const args = [
      "run_attack.py",
      url,
      "--iter",
      iterations.toString(),
      "--mutations",
      mutations.toString(),
      "--user_id",
      user_id
    ];

    console.log(`\n================================`);
    console.log(`[Frontend] Launching Agent`);
    console.log(`URL: ${url}`);
    console.log(`Headless: ${headless}`);
    console.log(`Iterations: ${iterations}`);
    console.log(`Mutations: ${mutations}`);
    console.log(`================================\n`);

    const child = spawn(pythonExecutable, args, {
      cwd: rootDir,
      env: {
        ...process.env,
        PLAYWRIGHT_HEADLESS: headless ? "true" : "false",
        PYTHONIOENCODING: "utf-8",
      }
    });

    const stream = new ReadableStream({
      start(controller) {
        child.stdout.on("data", (data) => {
          controller.enqueue(data);
        });
        child.stderr.on("data", (data) => {
          controller.enqueue(data);
        });
        child.on("close", (code) => {
          controller.close();
        });
        child.on("error", (err) => {
          controller.error(err);
        });
        req.signal.addEventListener("abort", () => {
          console.log("[Frontend] Client aborted stream, killing agent process...");
          child.kill();
        });
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error: any) {
    console.error("Error launching agent:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
