import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // BACKEND_URL is a server-side only variable (no NEXT_PUBLIC_ prefix).
  // Set it in Vercel's project environment variables to point at your
  // deployed FastAPI backend (Railway, Render, etc.).
  //
  // Vercel function timeout: 60s (Hobby) / 300s (Pro).
  // Long scans need a Pro plan or a lower --iter count.
  serverExternalPackages: [],
};

export default nextConfig;
