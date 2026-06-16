import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { url } = body;

    // Security validation — mirrors backend validation
    const safeTargets = ["chatbot", "rag", "tool_agent"];
    const isValidUrl = url.startsWith("http://") || url.startsWith("https://");
    const isSafeTarget = safeTargets.includes(url);

    if (!isValidUrl && !isSafeTarget) {
      return NextResponse.json(
        { success: false, error: "Invalid target. Must be a valid URL (http/https) or a predefined local target name." },
        { status: 400 }
      );
    }

    console.log(`[Frontend] Proxying attack request to backend: ${BACKEND_URL}/run`);
    console.log(`  URL: ${url} | Iterations: ${body.iterations} | Mutations: ${body.mutations}`);

    // Forward request to the FastAPI backend and stream the response back
    const backendResponse = await fetch(`${BACKEND_URL}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      // NOTE: Vercel function timeout is 60s on hobby, 300s on pro.
      // For long scans, ensure your Vercel plan matches expected scan duration.
      signal: req.signal,
    });

    if (!backendResponse.ok) {
      const errText = await backendResponse.text();
      console.error("[Frontend] Backend returned error:", errText);
      return NextResponse.json(
        { success: false, error: `Backend error: ${errText}` },
        { status: backendResponse.status }
      );
    }

    // Stream the backend response directly to the client
    return new Response(backendResponse.body, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error: any) {
    if (error.name === "AbortError") {
      // Client disconnected — this is expected, not an error
      return new Response(null, { status: 499 });
    }
    console.error("[Frontend] Error proxying to backend:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
