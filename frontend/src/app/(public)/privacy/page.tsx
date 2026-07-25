import Link from "next/link";
import { Shield, ArrowLeft, Lock, Database } from "lucide-react";

export const metadata = {
  title: "Privacy Policy | Aegis-Red",
  description: "Privacy Policy detailing telemetry, data handling, and tenant security for Aegis-Red Autonomous AI Red-Teaming Platform.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#060608] text-zinc-100 flex flex-col font-sans relative overflow-hidden">
      {/* Background radial ambient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-red-950/15 blur-[140px] pointer-events-none rounded-full" />

      {/* Header */}
      <header className="border-b border-zinc-800/60 bg-[#0a0a0f]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors text-sm font-mono">
            <ArrowLeft className="w-4 h-4" /> Back to Aegis-Red
          </Link>
          <div className="flex items-center gap-2 text-red-500 font-mono text-sm font-bold">
            <Shield className="w-4 h-4" /> Aegis-Red Security Governance
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-12 flex-1 relative z-10 space-y-8">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
            <Lock className="w-3.5 h-3.5" /> Effective Date: July 25, 2026
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-100 font-mono">
            Privacy Policy & Data Handling
          </h1>
          <p className="text-zinc-400 text-sm leading-relaxed">
            This policy describes how Aegis-Red handles account authentication, telemetry logging, attack session artifacts, and tenant isolation.
          </p>
        </div>

        <hr className="border-zinc-800/80" />

        <div className="space-y-8 text-zinc-300 text-sm leading-relaxed font-sans">
          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-zinc-100 font-mono flex items-center gap-2">
              <Database className="w-5 h-5 text-red-500" /> 1. Information We Collect
            </h2>
            <p>Aegis-Red collects minimal data required to execute autonomous security evaluations and generate audit reports:</p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400">
              <li><strong className="text-zinc-200">Account Identity</strong>: User email address and Supabase authentication UUID.</li>
              <li><strong className="text-zinc-200">Scan Session Targets</strong>: Target URLs, target titles, and target classification metadata.</li>
              <li><strong className="text-zinc-200">Attack Telemetry & Artifacts</strong>: Turn-by-turn payload execution logs, raw target responses, evaluation verdicts, and Markdown/HTML audit reports.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-zinc-100 font-mono">2. Tenant Data Isolation & Row Level Security (RLS)</h2>
            <p>
              All attack logs, findings, and stored reports are strictly isolated per tenant using Supabase Row Level Security (RLS) policies. Users can only read, write, or download scan artifacts that belong explicitly to their authenticated user UUID.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-zinc-100 font-mono">3. Data Retention & Deletion</h2>
            <p>
              Scan traces and penetration testing reports remain stored in your encrypted workspace until explicitly deleted. You may request full session record deletion or clear log telemetry directly through the application interface.
            </p>
          </section>
        </div>

        {/* Footer Link */}
        <div className="pt-8 border-t border-zinc-800/60 flex items-center justify-between text-xs font-mono text-zinc-500">
          <p>© 2026 Aegis-Red Framework. All rights reserved.</p>
          <Link href="/terms" className="text-zinc-400 hover:text-zinc-200 underline">
            Terms of Service
          </Link>
        </div>
      </main>
    </div>
  );
}
