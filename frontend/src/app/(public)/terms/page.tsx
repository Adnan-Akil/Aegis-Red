import Link from "next/link";
import { Shield, ArrowLeft, FileText, CheckCircle2 } from "lucide-react";

export const metadata = {
  title: "Terms of Service | Aegis-Red",
  description: "Terms of Service and Authorized Security Testing Policy for Aegis-Red Autonomous AI Red-Teaming Platform.",
};

export default function TermsPage() {
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
            <FileText className="w-3.5 h-3.5" /> Effective Date: July 25, 2026
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-100 font-mono">
            Terms of Service & Authorized Pen-Testing Policy
          </h1>
          <p className="text-zinc-400 text-sm leading-relaxed">
            Please read these Terms of Service carefully before accessing or executing security audits via the Aegis-Red platform.
          </p>
        </div>

        <hr className="border-zinc-800/80" />

        <div className="space-y-8 text-zinc-300 text-sm leading-relaxed font-sans">
          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-zinc-100 font-mono flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-red-500" /> 1. Explicit Scope & Authorization Requirement
            </h2>
            <p>
              Aegis-Red is an automated vulnerability assessment and AI agent red-teaming framework designed strictly for defensive security research, compliance auditing, and authorized penetration testing.
            </p>
            <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 text-red-200 text-xs font-mono space-y-2">
              <p className="font-bold uppercase tracking-wider">Mandatory Authorization Condition:</p>
              <p>
                By providing a target URL or endpoint to Aegis-Red, you explicitly warrant and represent that you possess verified legal ownership, system administration rights, or explicit written permission from the system owner to conduct security testing on the target application.
              </p>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-zinc-100 font-mono">2. Prohibited Uses</h2>
            <p>You strictly agree not to use Aegis-Red for any of the following unauthorized activities:</p>
            <ul className="list-disc pl-6 space-y-2 text-zinc-400">
              <li>Launching automated adversarial scans against third-party AI chatbots or infrastructure without explicit authorization.</li>
              <li>Attempting Denial-of-Service (DoS) attacks or deliberately impairing third-party availability.</li>
              <li>Exfiltrating, storing, or publishing real-world Personally Identifiable Information (PII) or confidential secrets obtained without consent.</li>
              <li>Bypassing system access controls for malicious, unlawful, or coercive purposes.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-zinc-100 font-mono">3. Limitation of Liability</h2>
            <p>
              Aegis-Red and its developers disclaim all liability for damages, system downtime, data corruption, or legal consequences resulting from unauthorized or improper use of the platform. Users assume 100% legal responsibility for all targets tested under their account credentials.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-zinc-100 font-mono">4. Responsible Disclosure</h2>
            <p>
              If Aegis-Red identifies zero-day vulnerabilities or systemic security risks in third-party target frameworks, operators are encouraged to follow Industry Standard Coordinated Vulnerability Disclosure (CVD) practices.
            </p>
          </section>
        </div>

        {/* Footer Link */}
        <div className="pt-8 border-t border-zinc-800/60 flex items-center justify-between text-xs font-mono text-zinc-500">
          <p>© 2026 Aegis-Red Framework. All rights reserved.</p>
          <Link href="/privacy" className="text-zinc-400 hover:text-zinc-200 underline">
            Privacy Policy
          </Link>
        </div>
      </main>
    </div>
  );
}
