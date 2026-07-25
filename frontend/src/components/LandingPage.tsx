"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, useScroll, useTransform, AnimatePresence, type Variants } from "framer-motion";
import { supabase } from "@/lib/supabase";
import { AuthModal } from "@/components/AuthModal";
import {
  ShieldCheck,
  Network,
  BarChart3,
  ChevronDown,
  Zap,
  Lock,
  Activity,
} from "lucide-react";

// ─── Fake terminal log lines ──────────────────────────────────────────────────
const LOG_LINES = [
  "[00:00:01] ► Initialising attack session · target=GPT-4o",
  "[00:00:02] ✓ Orchestrator online · agents=4 · strategy=multi-turn",
  "[00:00:03] ► Attacker-Agent dispatched · mutation=semantic-shift",
  "[00:00:04] ✓ Probe #001 sent · tokens=112",
  "[00:00:05] ✗ Response: refused · jailbreak=false",
  "[00:00:06] ► Judge-Agent evaluating · rubric=harm-taxonomy",
  "[00:00:07] ✓ Score: 2/10 · category=benign",
  "[00:00:08] ► Mutator applying role-injection delta",
  "[00:00:09] ✓ Probe #002 sent · tokens=189",
  "[00:00:10] ✓ Response: partial · jailbreak=partial",
  "[00:00:11] ► Escalating strategy · mode=adversarial-chain",
  "[00:00:12] ✓ Probe #003 sent · tokens=241",
  "[00:00:13] ✓ Response: accepted · jailbreak=TRUE ⚠",
  "[00:00:14] ► Logging breach event · session_id=AX-3812",
  "[00:00:15] ✓ Report generated · format=PDF · pages=6",
  "[00:00:16] ► Resetting payload · next_variant=cipher-obfuscation",
  "[00:00:17] ✓ Probe #004 sent · tokens=178",
  "[00:00:18] ✗ Response: refused · jailbreak=false",
  "[00:00:19] ► Orchestrator learning from refusal",
  "[00:00:20] ✓ Probe #005 sent · tokens=302",
];

// ─── Feature cards data ───────────────────────────────────────────────────────
const FEATURES = [
  {
    Icon: ShieldCheck,
    title: "Autonomous Pen-Testing",
    description:
      "Deploy AI agents that autonomously craft, fire, and evaluate adversarial probes against target LLMs — no human in the loop required.",
    accent: "rgba(220,38,38,0.15)",
    border: "rgba(220,38,38,0.25)",
    iconColor: "text-red-500",
  },
  {
    Icon: Network,
    title: "Multi-Agent Orchestration",
    description:
      "Attacker, Mutator, and Judge agents coordinate in real-time — adapting strategy mid-session based on live refusal signals.",
    accent: "rgba(168,85,247,0.12)",
    border: "rgba(168,85,247,0.22)",
    iconColor: "text-purple-400",
  },
  {
    Icon: BarChart3,
    title: "Live Session Reports",
    description:
      "Every probe, score, and breach event is logged and exportable. Generate PDF reports with jailbreak rates, vectors, and severity maps.",
    accent: "rgba(59,130,246,0.10)",
    border: "rgba(59,130,246,0.20)",
    iconColor: "text-blue-400",
  },
];

// ─── Stats ────────────────────────────────────────────────────────────────────
const STATS = [
  { value: "50+", label: "Attack Strategies" },
  { value: "12", label: "Agent Types" },
  { value: "99.2%", label: "Detection Coverage" },
  { value: "<1s", label: "Probe Latency" },
];

// ─── Animation variants ───────────────────────────────────────────────────────
const heroContainer: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.14, delayChildren: 0.25 },
  },
};
const heroItem: Variants = {
  hidden: { opacity: 0, y: 36 },
  show: { opacity: 1, y: 0, transition: { duration: 0.75, ease: [0.22, 1, 0.36, 1] as [number, number, number, number] } },
};

export function LandingPage() {
  const router = useRouter();
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"signin" | "signup">("signin");
  const [authChecked, setAuthChecked] = useState(false);

  // Terminal scroll ref
  const terminalRef = useRef<HTMLDivElement>(null);

  // Parallax on hero
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 600], [0, 80]);

  // If already authenticated, push straight to dashboard
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.replace("/dashboard");
      } else {
        setAuthChecked(true);
      }
    });

    // Also listen for sign-in from AuthModal
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        router.replace("/dashboard");
      }
    });
    return () => subscription.unsubscribe();
  }, [router]);

  // Auto-scroll terminal
  useEffect(() => {
    const el = terminalRef.current;
    if (!el) return;
    const interval = setInterval(() => {
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 4) {
        el.scrollTop = 0;
      } else {
        el.scrollTop += 1;
      }
    }, 35);
    return () => clearInterval(interval);
  }, []);

  const openSignIn = () => { setModalMode("signin"); setModalOpen(true); };
  const openSignUp = () => { setModalMode("signup"); setModalOpen(true); };

  // Don't flash landing to authenticated users
  if (!authChecked) return null;

  return (
    <div className="landing-scroll min-h-screen w-full overflow-x-hidden text-zinc-300 font-sans">
      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative h-screen w-full flex flex-col items-center justify-center overflow-hidden">
        {/* Background image with parallax */}
        <motion.div
          className="absolute inset-0 z-0"
          style={{
            y: heroY,
            backgroundImage: "url('/bg_picture.jpg')",
            backgroundSize: "cover",
            backgroundPosition: "center",
            filter: "blur(6px) brightness(0.45) saturate(0.8)",
            transform: "scale(1.12)",
            willChange: "transform",
          }}
        />

        {/* Dark overlay */}
        <div className="absolute inset-0 z-0 bg-black/40" />

        {/* Vignette */}
        <div
          className="absolute inset-0 z-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.72) 100%)" }}
        />

        {/* Ambient orbs */}
        <motion.div
          className="absolute pointer-events-none rounded-full z-0"
          style={{ width: 600, height: 600, background: "radial-gradient(circle, rgba(220,38,38,0.07) 0%, transparent 70%)", top: "10%", left: "5%" }}
          animate={{ x: [0, 28, -18, 0], y: [0, -22, 18, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute pointer-events-none rounded-full z-0"
          style={{ width: 480, height: 480, background: "radial-gradient(circle, rgba(168,85,247,0.06) 0%, transparent 70%)", bottom: "12%", right: "8%" }}
          animate={{ x: [0, -22, 14, 0], y: [0, 18, -24, 0] }}
          transition={{ duration: 22, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        />
        <motion.div
          className="absolute pointer-events-none rounded-full z-0"
          style={{ width: 320, height: 320, background: "radial-gradient(circle, rgba(59,130,246,0.04) 0%, transparent 70%)", top: "55%", left: "40%" }}
          animate={{ x: [0, 14, -10, 0], y: [0, -14, 12, 0] }}
          transition={{ duration: 14, repeat: Infinity, ease: "easeInOut", delay: 5 }}
        />

        {/* Scan-line overlay */}
        <div className="absolute inset-0 z-1 pointer-events-none scanlines-overlay" />

        {/* Hero content */}
        <motion.div
          className="relative z-10 text-center flex flex-col items-center px-4"
          variants={heroContainer}
          initial="hidden"
          animate="show"
        >
          {/* Badge */}
          <motion.div variants={heroItem}>
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono tracking-widest uppercase mb-8"
              style={{
                background: "rgba(220,38,38,0.12)",
                border: "1px solid rgba(220,38,38,0.3)",
                color: "rgba(239,68,68,0.9)",
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse inline-block" />
              AI Security Intelligence Platform
            </span>
          </motion.div>

          {/* Logo / Title */}
          <motion.h1
            variants={heroItem}
            className="text-white select-none"
            style={{
              fontFamily: "var(--font-chaste)",
              fontSize: "clamp(3.5rem, 10vw, 8rem)",
              letterSpacing: "0.18em",
              lineHeight: 1,
              textShadow: "0 0 80px rgba(220,38,38,0.25), 0 2px 40px rgba(0,0,0,0.8)",
            }}
          >
            Aegis-Red
          </motion.h1>

          {/* Divider line */}
          <motion.div
            variants={heroItem}
            className="my-6 flex items-center gap-4"
          >
            <div className="h-px w-16 bg-gradient-to-r from-transparent to-zinc-600" />
            <Zap className="w-3 h-3 text-red-500 opacity-80" />
            <div className="h-px w-16 bg-gradient-to-l from-transparent to-zinc-600" />
          </motion.div>

          {/* Subtitle */}
          <motion.p
            variants={heroItem}
            className="text-zinc-400 max-w-xl text-base sm:text-lg leading-relaxed mb-10 uppercase tracking-widest font-mono text-xs sm:text-sm text-zinc-400/90"
          >
            Deploy autonomous AI agents to pen-test, probe, and report on large language model vulnerabilities.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div variants={heroItem} className="flex flex-col sm:flex-row items-center gap-3">
            <motion.button
              onClick={openSignIn}
              whileHover={{ scale: 1.04, boxShadow: "0 0 28px rgba(255,255,255,0.12)" }}
              whileTap={{ scale: 0.97 }}
              className="px-8 py-3 rounded-xl text-sm font-semibold bg-white text-black tracking-wide transition-colors cursor-pointer min-w-[160px]"
            >
              Sign In
            </motion.button>
            <motion.button
              onClick={openSignUp}
              whileHover={{ scale: 1.04, boxShadow: "0 0 28px rgba(220,38,38,0.2)" }}
              whileTap={{ scale: 0.97 }}
              className="px-8 py-3 rounded-xl text-sm font-semibold tracking-wide cursor-pointer min-w-[160px] transition-colors"
              style={{
                background: "rgba(220,38,38,0.12)",
                border: "1px solid rgba(220,38,38,0.35)",
                color: "rgba(252,165,165,0.95)",
              }}
            >
              Request Access
            </motion.button>
          </motion.div>
        </motion.div>

        {/* Scroll cue */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-1 text-zinc-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8, duration: 0.8 }}
        >
          <span className="text-[10px] tracking-widest uppercase font-mono">Scroll</span>
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          >
            <ChevronDown className="w-4 h-4" />
          </motion.div>
        </motion.div>
      </section>

      {/* ── STATS STRIP ──────────────────────────────────────────────────── */}
      <section
        className="relative w-full py-12 overflow-hidden"
        style={{ background: "rgba(0,0,0,0.6)", borderTop: "1px solid rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.04)" }}
      >
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-4 gap-8">
          {STATS.map(({ value, label }, i) => (
            <motion.div
              key={label}
              className="flex flex-col items-center text-center"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.55, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] }}
            >
              <span
                className="text-3xl font-bold text-white"
                style={{ fontFamily: "var(--font-chaste)", letterSpacing: "0.05em" }}
              >
                {value}
              </span>
              <span className="text-xs text-zinc-500 mt-1 font-mono tracking-widest uppercase">
                {label}
              </span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ─────────────────────────────────────────────────────── */}
      <section className="relative w-full py-28 px-6" style={{ background: "#080809" }}>
        {/* Section heading */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-[10px] font-mono tracking-[0.35em] uppercase text-zinc-500/60 mb-2">Capabilities</p>
          <h2 className="text-2xl sm:text-3xl font-semibold text-zinc-200 opacity-90" style={{ letterSpacing: "0.04em" }}>
            Built for adversarial AI research
          </h2>
          <p className="text-zinc-500 text-sm mt-3 max-w-md mx-auto leading-relaxed">
            Aegis-Red gives security teams the infrastructure to probe, measure, and report on LLM weaknesses — at scale.
          </p>
        </motion.div>

        {/* Feature cards */}
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-5">
          {FEATURES.map(({ Icon, title, description, accent, border, iconColor }, i) => (
            <motion.div
              key={title}
              className="relative rounded-2xl p-7 flex flex-col gap-4 group"
              style={{
                background: `linear-gradient(135deg, rgba(14,14,16,0.9) 0%, ${accent} 100%)`,
                border: `1px solid ${border}`,
                backdropFilter: "blur(12px)",
              }}
              initial={{ opacity: 0, y: 36 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.65, delay: i * 0.12, ease: [0.22, 1, 0.36, 1] }}
              whileHover={{ y: -4, transition: { duration: 0.3, ease: "easeOut" } }}
            >
              {/* Icon bubble */}
              <div
                className="w-11 h-11 rounded-xl flex items-center justify-center"
                style={{ background: accent, border: `1px solid ${border}` }}
              >
                <Icon className={`w-5 h-5 ${iconColor}`} />
              </div>

              <div>
                <h3 className="text-white font-semibold text-base mb-2">{title}</h3>
                <p className="text-zinc-500 text-sm leading-relaxed">{description}</p>
              </div>

              {/* Hover shimmer */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                style={{ background: `radial-gradient(circle at 50% 0%, ${accent} 0%, transparent 60%)` }}
              />
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── TERMINAL PREVIEW ─────────────────────────────────────────────── */}
      <section
        className="relative w-full py-24 px-6 overflow-hidden"
        style={{ background: "#0b0b0d" }}
      >
        {/* Decorative glow behind terminal */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse at 50% 50%, rgba(220,38,38,0.04) 0%, transparent 65%)" }}
        />

        <div className="max-w-4xl mx-auto">
          {/* Section heading */}
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="text-xs font-mono tracking-[0.3em] uppercase text-zinc-600 mb-3">Live Intelligence</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white" style={{ letterSpacing: "0.04em" }}>
              Watch the agents work
            </h2>
            <p className="text-zinc-500 text-sm mt-3 max-w-md mx-auto leading-relaxed">
              Every session streams real-time probe logs, scoring events, and breach detections — all captured for your audit trail.
            </p>
          </motion.div>

          {/* Terminal window */}
          <motion.div
            className="rounded-2xl overflow-hidden shadow-2xl"
            style={{
              border: "1px solid rgba(255,255,255,0.07)",
              boxShadow: "0 40px 120px rgba(0,0,0,0.8), 0 0 0 1px rgba(220,38,38,0.06)",
            }}
            initial={{ opacity: 0, y: 40, scale: 0.97 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* Terminal title bar */}
            <div
              className="flex items-center gap-2 px-4 py-3"
              style={{ background: "rgba(20,20,24,0.95)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}
            >
              <div className="w-3 h-3 rounded-full bg-red-500/70" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/40" />
              <div className="w-3 h-3 rounded-full bg-green-500/40" />
              <span className="ml-3 text-xs text-zinc-600 font-mono tracking-widest">aegis-red · attack-session · AX-3812</span>
              <div className="ml-auto flex items-center gap-1.5 text-zinc-600">
                <Activity className="w-3 h-3 text-red-500 animate-pulse" />
                <span className="text-[10px] font-mono text-red-500/80">LIVE</span>
              </div>
            </div>

            {/* Terminal body */}
            <div
              ref={terminalRef}
              className="overflow-hidden"
              style={{
                background: "rgba(8,8,10,0.97)",
                height: "280px",
                maskImage: "linear-gradient(to bottom, transparent 0%, black 8%, black 88%, transparent 100%)",
              }}
            >
              <div className="p-5 font-mono text-xs leading-7">
                {/* Repeat lines for seamless scroll */}
                {[...LOG_LINES, ...LOG_LINES].map((line, i) => {
                  const isSuccess = line.includes("✓");
                  const isError = line.includes("✗");
                  const isBreach = line.includes("TRUE");
                  const isLabel = line.includes("►");
                  return (
                    <div key={i} className={`
                      ${isBreach ? "text-red-400 font-semibold" : ""}
                      ${isSuccess && !isBreach ? "text-green-400/80" : ""}
                      ${isError ? "text-zinc-500" : ""}
                      ${isLabel && !isSuccess && !isError && !isBreach ? "text-zinc-400" : ""}
                    `}>
                      {line}
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────────────────────── */}
      <section
        className="relative w-full py-24 px-6"
        style={{ background: "#080809" }}
      >
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="text-center mb-14"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.65 }}
          >
            <p className="text-[10px] font-mono tracking-[0.35em] uppercase text-zinc-500/60 mb-2">Workflow</p>
            <h2 className="text-2xl sm:text-3xl font-semibold text-zinc-200 opacity-90" style={{ letterSpacing: "0.04em" }}>
              From target to report in minutes
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                Icon: Lock,
                title: "Configure Target",
                desc: "Point Aegis-Red at any LLM endpoint or hosted model. Set your attack budget, strategy mix, and severity thresholds.",
              },
              {
                step: "02",
                Icon: Zap,
                title: "Deploy Agents",
                desc: "The orchestrator spawns Attacker, Mutator, and Judge agents. They collaborate in real-time to craft and evaluate adversarial probes.",
              },
              {
                step: "03",
                Icon: BarChart3,
                title: "Export Report",
                desc: "When the session ends, download a structured PDF with breach events, jailbreak rates, severity maps, and mitigation recommendations.",
              },
            ].map(({ step, Icon, title, desc }, i) => (
              <motion.div
                key={step}
                className="relative flex flex-col gap-4 p-7 rounded-2xl"
                style={{ background: "rgba(14,14,16,0.85)", border: "1px solid rgba(255,255,255,0.05)" }}
                initial={{ opacity: 0, y: 28 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: i * 0.13, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="flex items-start justify-between">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <Icon className="w-4 h-4 text-zinc-400" />
                  </div>
                  <span
                    className="text-4xl font-bold leading-none"
                    style={{ fontFamily: "var(--font-chaste)", color: "rgba(255,255,255,0.05)", letterSpacing: "0.05em" }}
                  >
                    {step}
                  </span>
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm mb-2">{title}</h3>
                  <p className="text-zinc-500 text-xs leading-relaxed">{desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ────────────────────────────────────────────────────── */}
      <section
        className="relative w-full py-32 px-6 overflow-hidden flex flex-col items-center justify-center text-center"
        style={{ background: "#0b0b0d", borderTop: "1px solid rgba(255,255,255,0.04)" }}
      >
        {/* Glow */}
        <div
          className="absolute inset-0 pointer-events-none z-0"
          style={{ background: "radial-gradient(ellipse at 50% 80%, rgba(220,38,38,0.12) 0%, transparent 60%)" }}
        />

        <motion.div
          className="relative z-10 max-w-lg"
          initial={{ opacity: 0, y: 32 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-[10px] font-mono tracking-[0.35em] uppercase text-zinc-500/60 mb-3">Ready to deploy?</p>
          <h2
            className="text-3xl sm:text-4xl font-semibold text-zinc-200 mb-5"
            style={{ fontFamily: "var(--font-chaste)", letterSpacing: "0.1em", lineHeight: 1.1 }}
          >
            Aegis-Red
          </h2>
          <p className="text-zinc-400 text-sm leading-relaxed mb-10">
            Authorised security research only. Request access to begin probing your AI systems with the full suite of autonomous agents.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <motion.button
              onClick={openSignIn}
              whileHover={{ scale: 1.04, boxShadow: "0 0 32px rgba(255,255,255,0.14)" }}
              whileTap={{ scale: 0.97 }}
              className="px-10 py-3.5 rounded-xl text-sm font-semibold bg-white text-black tracking-wide cursor-pointer min-w-[180px]"
            >
              Sign In
            </motion.button>
            <motion.button
              onClick={openSignUp}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              className="px-10 py-3.5 rounded-xl text-sm font-semibold tracking-wide cursor-pointer min-w-[180px]"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.10)",
                color: "rgba(212,212,216,0.9)",
              }}
            >
              Request Access
            </motion.button>
          </div>
        </motion.div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer
        className="w-full py-8 px-6 flex flex-col sm:flex-row items-center justify-between gap-3 relative z-10"
        style={{ background: "#080809", borderTop: "1px solid rgba(255,255,255,0.04)" }}
      >
        <span
          className="text-zinc-200 text-sm font-bold tracking-widest uppercase font-mono drop-shadow-sm"
          style={{ fontFamily: "var(--font-chaste)", letterSpacing: "0.2em" }}
        >
          Aegis-Red
        </span>
        <span className="text-zinc-400 text-xs font-mono">
          © 2026 · For authorised AI security research only.
        </span>
      </footer>

      {/* ── AUTH MODAL ───────────────────────────────────────────────────── */}
      <AuthModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        defaultMode={modalMode}
      />
    </div>
  );
}
