import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

// Server-side Supabase client (uses service role or anon key to verify JWTs)
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// ─── Server-side limits (cannot be overridden by the client) ──────────────────
const MAX_MUTATIONS = 5;
const MAX_ITERATIONS = 15;

// ─── SSRF guard — block private/internal network targets ─────────────────────
const BLOCKED_PATTERNS = [
  /^https?:\/\/localhost(:\d+)?(\/|$)/i,
  /^https?:\/\/127\.\d+\.\d+\.\d+(:\d+)?(\/|$)/,
  /^https?:\/\/0\.0\.0\.0(:\d+)?(\/|$)/,
  /^https?:\/\/10\.\d+\.\d+\.\d+(:\d+)?(\/|$)/,
  /^https?:\/\/172\.(1[6-9]|2\d|3[01])\.\d+\.\d+(:\d+)?(\/|$)/,
  /^https?:\/\/192\.168\.\d+\.\d+(:\d+)?(\/|$)/,
  /^https?:\/\/169\.254\.\d+\.\d+(:\d+)?(\/|$)/, // AWS metadata / link-local
  /^https?:\/\/\[::1\](:\d+)?(\/|$)/,             // IPv6 loopback
  /^https?:\/\/\[fc[0-9a-f]{2}:/i,                // IPv6 ULA
];

function isSSRFTarget(url: string): boolean {
  return BLOCKED_PATTERNS.some((re) => re.test(url));
}

// ─── Allowed local benchmark names (no SSRF risk) ─────────────────────────────
const SAFE_LOCAL_NAMES = new Set(["chatbot", "rag", "tool_agent"]);

export async function POST(req: Request) {
  // ── 1. Verify Supabase session from Authorization header ──────────────────
  const authHeader = req.headers.get("Authorization");
  const token = authHeader?.startsWith("Bearer ") ? authHeader.slice(7) : null;

  if (!token) {
    return NextResponse.json(
      { success: false, error: "Unauthorized: missing session token." },
      { status: 401 }
    );
  }

  const { data: { user }, error: authError } = await supabaseAdmin.auth.getUser(token);
  if (authError || !user) {
    return NextResponse.json(
      { success: false, error: "Unauthorized: invalid or expired session." },
      { status: 401 }
    );
  }

  // ── 2. Parse and whitelist body — never forward unknown fields ────────────
  let rawBody: Record<string, unknown>;
  try {
    rawBody = await req.json();
  } catch {
    return NextResponse.json(
      { success: false, error: "Invalid request body." },
      { status: 400 }
    );
  }

  const url = typeof rawBody.url === "string" ? rawBody.url.trim() : "";
  const headless = rawBody.headless !== false; // default true
  const mutations = Math.min(
    MAX_MUTATIONS,
    Math.max(1, Number(rawBody.mutations) || 3)
  );
  const iterations = Math.min(
    MAX_ITERATIONS,
    Math.max(1, Number(rawBody.iterations) || 5)
  );

  // ── 3. Validate target URL ────────────────────────────────────────────────
  const isValidHttpUrl = url.startsWith("http://") || url.startsWith("https://");
  const isSafeLocalName = SAFE_LOCAL_NAMES.has(url);

  if (!isValidHttpUrl && !isSafeLocalName) {
    return NextResponse.json(
      { success: false, error: "Invalid target. Must be a valid http/https URL or a predefined local target name." },
      { status: 400 }
    );
  }

  const isDev = process.env.NODE_ENV !== "production";
  if (!isDev && isValidHttpUrl && isSSRFTarget(url)) {
    return NextResponse.json(
      { success: false, error: "Target URL points to a private or restricted network address." },
      { status: 400 }
    );
  }

  // ── 4. Build the safe, whitelisted payload ────────────────────────────────
  const safePayload = {
    url,
    headless,
    mutations,
    iterations,
    user_id: user.id, // use the verified user ID from the JWT, not client-supplied
  };

  // ── 5. Forward to backend ─────────────────────────────────────────────────
  try {
    const backendResponse = await fetch(`${BACKEND_URL}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(safePayload),
      signal: req.signal,
    });

    if (!backendResponse.ok) {
      const errText = await backendResponse.text();
      return NextResponse.json(
        { success: false, error: "Backend returned an error. Check server logs." },
        { status: backendResponse.status }
      );
    }

    return new Response(backendResponse.body, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
        "Connection": "keep-alive",
      },
    });
  } catch (error: any) {
    if (error.name === "AbortError") {
      return new Response(null, { status: 499 });
    }
    return NextResponse.json(
      { success: false, error: "An internal error occurred." },
      { status: 500 }
    );
  }
}
