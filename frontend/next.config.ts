import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";

const securityHeaders = [
  // Anti-clickjacking — prevent the app from being embedded in an iframe
  { key: "X-Frame-Options", value: "DENY" },
  // Prevent MIME-type sniffing
  { key: "X-Content-Type-Options", value: "nosniff" },
  // Don't send Referer header to cross-origin destinations
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // Disable unnecessary browser features
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  },
  // Content Security Policy
  // - script-src: unsafe-inline required for Next.js hydration. unsafe-eval added in dev mode for React.
  // - frame-ancestors: none (belt-and-suspenders with X-Frame-Options)
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
      "style-src 'self' 'unsafe-inline' fonts.googleapis.com",
      "font-src 'self' fonts.gstatic.com data:",
      "img-src 'self' data: blob: *.supabase.co",
      "connect-src 'self' *.supabase.co wss://*.supabase.co",
      "media-src 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
      "upgrade-insecure-requests",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  // BACKEND_URL is a server-side only variable (no NEXT_PUBLIC_ prefix).
  // Set it in Vercel's project environment variables to point at your
  // deployed FastAPI backend (Railway, Render, etc.).
  //
  // Vercel function timeout: 60s (Hobby) / 300s (Pro).
  // Long scans need a Pro plan or a lower --iter count.
  serverExternalPackages: [],

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
