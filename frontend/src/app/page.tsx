"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Square, ChevronUp, ChevronDown } from "lucide-react";
import { useAppContext } from "@/app/context";
import { supabase } from "@/lib/supabase";
import { useRouter } from "next/navigation";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function formatTime(s: number) {
  const m = Math.floor(s / 60).toString().padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}

function getHostname(url: string) {
  try { return new URL(url).hostname || url; } catch { return url; }
}

// ─── Scroll-wheel control ─────────────────────────────────────────────────────
function useScrollControl(onDelta: (dir: 1 | -1) => void) {
  const ref = useRef<HTMLDivElement>(null);
  const handler = useCallback((e: WheelEvent) => {
    e.preventDefault();
    onDelta(e.deltaY > 0 ? -1 : 1);
  }, [onDelta]);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.addEventListener("wheel", handler, { passive: false });
    return () => el.removeEventListener("wheel", handler);
  }, [handler]);
  return ref;
}

// ─── ModeBox ───────────────────────────────────────────────────────────────────
function ModeBox({ id, value, onChange }: { id?: string; value: boolean; onChange: (v: boolean) => void }) {
  const [dir, setDir] = useState<1 | -1>(1);
  const handleDelta = useCallback((d: 1 | -1) => {
    setDir(d);
    if (d === 1) onChange(true); else onChange(false);
  }, [onChange]);
  const scrollRef = useScrollControl(handleDelta);
  const label = value ? "Headless" : "Headed";
  return (
    <div id={id} ref={scrollRef}
      className="flex-1 flex flex-col px-3 py-2.5 rounded-lg cursor-ns-resize select-none relative overflow-hidden group"
      style={{ background: "rgba(14,14,16,0.48)", backdropFilter: "blur(10px)", WebkitBackdropFilter: "blur(10px)", border: "1px solid rgba(255,255,255,0.06)", minWidth: 0 }}>
      <span className="text-[9px] uppercase tracking-widest text-zinc-300 font-semibold mb-1.5">Browser Mode</span>
      <div className="flex items-center justify-between gap-2 overflow-hidden">
        <div className="relative h-5 flex-1 overflow-hidden flex items-center">
          <AnimatePresence mode="popLayout" custom={dir}>
            <motion.span key={label} custom={dir}
              variants={{ enter: (d: number) => ({ y: d > 0 ? -18 : 18, opacity: 0 }), center: { y: 0, opacity: 1 }, exit: (d: number) => ({ y: d > 0 ? 18 : -18, opacity: 0 }) }}
              initial="enter" animate="center" exit="exit"
              transition={{ type: "spring", stiffness: 380, damping: 30 }}
              className="text-[13px] font-medium text-zinc-200 absolute whitespace-nowrap">
              {label}
            </motion.span>
          </AnimatePresence>
        </div>
        <div className="flex flex-col items-center shrink-0">
          <button onClick={() => { setDir(1); onChange(true); }} tabIndex={-1} className="text-zinc-600 hover:text-zinc-300 transition-colors leading-none"><ChevronUp className="w-3 h-3" strokeWidth={2.5} /></button>
          <button onClick={() => { setDir(-1); onChange(false); }} tabIndex={-1} className="text-zinc-600 hover:text-zinc-300 transition-colors leading-none"><ChevronDown className="w-3 h-3" strokeWidth={2.5} /></button>
        </div>
      </div>
    </div>
  );
}

// ─── StepperBox ────────────────────────────────────────────────────────────────────
function StepperBox({ id, label, value, min, max, onChange }: { id?: string; label: string; value: number; min: number; max: number; onChange: (v: number) => void }) {
  const [dir, setDir] = useState<1 | -1>(1);
  const step = useCallback((d: 1 | -1) => {
    const next = Math.min(max, Math.max(min, value + d));
    if (next !== value) { setDir(d); onChange(next); }
  }, [value, min, max, onChange]);
  const scrollRef = useScrollControl(step);
  return (
    <div id={id} ref={scrollRef}
      className="flex-1 flex flex-col px-3 py-2.5 rounded-lg cursor-ns-resize select-none relative overflow-hidden group"
      style={{ background: "rgba(14,14,16,0.48)", backdropFilter: "blur(10px)", WebkitBackdropFilter: "blur(10px)", border: "1px solid rgba(255,255,255,0.06)", minWidth: 0 }}>
      <span className="text-[9px] uppercase tracking-widest text-zinc-300 font-semibold mb-1.5">{label}</span>
      <div className="flex items-center justify-between gap-2 overflow-hidden">
        <div className="relative h-5 flex-1 overflow-hidden flex items-center">
          <AnimatePresence mode="popLayout" custom={dir}>
            <motion.span key={value} custom={dir}
              variants={{ enter: (d: number) => ({ y: d > 0 ? -18 : 18, opacity: 0 }), center: { y: 0, opacity: 1 }, exit: (d: number) => ({ y: d > 0 ? 18 : -18, opacity: 0 }) }}
              initial="enter" animate="center" exit="exit"
              transition={{ type: "spring", stiffness: 380, damping: 30 }}
              className="text-[13px] font-semibold text-zinc-200 absolute tabular-nums">
              {value}
            </motion.span>
          </AnimatePresence>
        </div>
        <div className="flex flex-col items-center shrink-0">
          <button onClick={() => step(1)} disabled={value >= max} tabIndex={-1} className="text-zinc-600 hover:text-zinc-300 disabled:opacity-20 transition-colors leading-none"><ChevronUp className="w-3 h-3" strokeWidth={2.5} /></button>
          <button onClick={() => step(-1)} disabled={value <= min} tabIndex={-1} className="text-zinc-600 hover:text-zinc-300 disabled:opacity-20 transition-colors leading-none"><ChevronDown className="w-3 h-3" strokeWidth={2.5} /></button>
        </div>
      </div>
    </div>
  );
}

// ─── Stat Bar ─────────────────────────────────────────────────────────────────
function StatBar({ label, value, max, display, color }: {
  label: string; value: number; max: number; display: string;
  color: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between items-center">
        <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold">{label}</span>
        <span className="text-[11px] text-zinc-300 font-semibold tabular-nums">{display}</span>
      </div>
      <div className="relative h-1 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <motion.div
          className="absolute left-0 top-0 h-full rounded-full"
          style={{ background: color }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 120, damping: 20 }}
        />
      </div>
    </div>
  );
}

// ─── Log line color ───────────────────────────────────────────────────────────
function logLineStyle(line: string): string {
  if (line.includes("🚨")) return "text-red-400 font-semibold";
  if (line.includes("✅") || line.includes("SUCCESS")) return "text-emerald-400/80";
  if (line.includes("🗡️")) return "text-rose-400/80";
  if (line.includes("⚠️")) return "text-amber-400/70";
  if (line.includes("❌")) return "text-red-400/70";
  if (line.includes("🔍") || line.includes("🧠") || line.includes("🕵️")) return "text-sky-400/60";
  if (line.includes("🚀") || line.includes("🎯")) return "text-violet-400/70";
  if (line.includes("===")) return "text-zinc-600";
  return "text-zinc-500";
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function LandingPage() {
  const router = useRouter();
  const {
    userName,
    headlessMode, setHeadlessMode,
    maxMutations, setMaxMutations,
    maxIterations, setMaxIterations,
    isScanning, setIsScanning,
    statusText, setStatusText,
    scanUrl: url, setScanUrl: setUrl,
    targetName, setTargetName,
    elapsedSeconds, setElapsedSeconds,
    currentIteration, setCurrentIteration,
    currentMutation, setCurrentMutation,
    currentSeverity, setCurrentSeverity,
    logLines, setLogLines,
  } = useAppContext();

  const abortControllerRef = useRef<AbortController | null>(null);
  const scanStartTimeRef = useRef<number>(0);
  const logEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Auto-scroll log to bottom ──
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logLines]);

  // ── Elapsed timer ──
  useEffect(() => {
    if (isScanning) {
      setElapsedSeconds(0);
      timerRef.current = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isScanning]);

  const resetMetrics = () => {
    setTargetName("");
    setElapsedSeconds(0);
    setCurrentIteration(0);
    setCurrentMutation(0);
    setCurrentSeverity(0);
    setLogLines([]);
  };

  const handleStop = () => {
    if (Date.now() - scanStartTimeRef.current < 500) return;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    if (isScanning) { handleStop(); return; }

    resetMetrics();
    setIsScanning(true);
    setStatusText("Initializing attack sequence...");
    abortControllerRef.current = new AbortController();
    scanStartTimeRef.current = Date.now();

    // Derive initial target name from URL right away
    setTargetName(getHostname(url));

    let wasCompleted = false;
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("No authenticated user found");

      // Retrieve the live session token to send as a Bearer token
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token) throw new Error("No active session token");

      const response = await fetch("/api/run", {
        method: "POST",
        signal: abortControllerRef.current.signal,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ url: url.trim(), headless: headlessMode, mutations: maxMutations, iterations: maxIterations, user_id: user.id }),
      });

      if (!response.ok) {
        let errData: any = {};
        try { errData = await response.json(); } catch {}
        throw new Error(errData.error || `Failed to start agent: ${response.statusText}`);
      }
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let partialData = "";
        let mutCount = 0;

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            wasCompleted = true;
            break;
          }
          partialData += decoder.decode(value, { stream: true });
          const lines = partialData.split("\n");
          partialData = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) continue;

            // Append to log
            setLogLines(prev => [...prev, line]);

            // Parse metrics
            // Target name (override from stream)
            const targetMatch = line.match(/🎯 Target: (.+?) \(/);
            if (targetMatch) setTargetName(targetMatch[1].trim());

            // Iteration — reset mutation counter
            const iterMatch = line.match(/\[Iteration (\d+)\]/);
            if (iterMatch) {
              setCurrentIteration(parseInt(iterMatch[1]));
              mutCount = 0;
              setCurrentMutation(0);
            }

            // New attack attempt — increment mutation
            if (line.includes("🗡️ Attack:")) {
              mutCount += 1;
              setCurrentMutation(mutCount);
            }

            // Verdict score → severity
            const scoreMatch = line.match(/Score\s+([\d.]+)/);
            if (scoreMatch) {
              setCurrentSeverity(Math.round(parseFloat(scoreMatch[1]) * 100));
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== "AbortError") {
        console.error(error);
        setLogLines(prev => [...prev, `❌ Error: ${error.message}`]);
      }
    } finally {
      if (!wasCompleted) {
        setIsScanning(false);
        setTimeout(() => setStatusText(""), 4000);
        setUrl("");
      }
    }

    if (wasCompleted) {
      setTimeout(() => router.push("/reports"), 800);
      // Reset the component state in the background after routing away
      setTimeout(() => {
        setIsScanning(false);
        setStatusText("");
        setUrl("");
      }, 3000);
    }
  };

  // ── Severity color ──
  const severityColor =
    currentSeverity >= 70 ? "linear-gradient(to right, #ef4444, #b91c1c)" :
    currentSeverity >= 30 ? "linear-gradient(to right, #f59e0b, #d97706)" :
    "linear-gradient(to right, #10b981, #059669)";

  return (
    <div className="h-full w-full flex flex-col overflow-hidden relative" style={{ paddingTop: isScanning ? 0 : "8%" }}>

      {/* Ambient orbs — idle only */}
      {!isScanning && (
        <>
          <motion.div className="absolute pointer-events-none rounded-full"
            style={{ width: 440, height: 440, background: "radial-gradient(circle, rgba(220,38,38,0.055) 0%, transparent 70%)", top: "18%", left: "12%" }}
            animate={{ x: [0, 20, -12, 0], y: [0, -16, 14, 0] }}
            transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }} />
          <motion.div className="absolute pointer-events-none rounded-full"
            style={{ width: 340, height: 340, background: "radial-gradient(circle, rgba(168,85,247,0.05) 0%, transparent 70%)", bottom: "20%", right: "14%" }}
            animate={{ x: [0, -16, 10, 0], y: [0, 14, -18, 0] }}
            transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 2 }} />
        </>
      )}

      {/* Vignette */}
      <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.62) 100%)" }} />

      {/* ── IDLE: centered greeting + input ── */}
      <AnimatePresence>
        {!isScanning && (
          <motion.div
            key="idle-hero"
            className="absolute inset-0 flex flex-col items-center justify-center px-6 z-10"
            style={{ paddingTop: "8%" }}
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, y: -8, transition: { duration: 0.35, ease: "easeIn" } }}
          >
            {/* Greeting */}
            <motion.div className="mb-5 text-center w-full max-w-2xl"
              initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: -64 }}
              transition={{ duration: 0.5, ease: "easeOut" }}>
              <h2 className="font-medium text-white mb-2 tracking-tight" style={{ fontSize: "2.43rem" }}>{getGreeting()}, {userName}.</h2>
              <p className="text-zinc-400" style={{ fontSize: "1.08rem" }}>Probe. Exploit. Harden. — AI red-teaming with surgical precision.</p>
            </motion.div>

            {/* Textbox */}
            <motion.div className="relative w-full max-w-2xl group"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: -24 }}
              transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}>
              {/* Idle glow */}
              <div className="absolute -inset-4 bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-xl blur-3xl opacity-[0.13] group-focus-within:opacity-28 transition-opacity duration-500 pointer-events-none z-0" />
              <div className="absolute -inset-1.5 bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-lg blur-xl opacity-22 group-focus-within:opacity-45 transition-opacity duration-500 pointer-events-none z-0" />
              <div className="absolute -inset-[1px] bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-lg opacity-48 group-focus-within:opacity-72 transition-opacity duration-500 pointer-events-none z-0" />

              <form onSubmit={handleScan}
                id="tour-url-input"
                className="relative z-10 w-full rounded-lg p-1 flex items-center shadow-sm"
                style={{ background: "rgba(16,16,18,0.86)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <input type="url" placeholder="Enter target AI URL..." value={url} onChange={e => setUrl(e.target.value)} required
                  className="flex-1 bg-transparent border-none outline-none text-zinc-200 placeholder-white/40 px-4 py-3.5 text-[15px]" />
                <motion.button id="tour-launch-btn" type="submit" disabled={!url} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  className="bg-zinc-800/90 text-white hover:bg-zinc-700 px-4 py-2 mr-1 rounded-md font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center h-10 w-12">
                  <ChevronRight className="w-5 h-5" />
                </motion.button>
              </form>
            </motion.div>

            {/* Config row */}
            <motion.div className="w-full max-w-2xl mt-3 flex gap-2"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: -24 }}
              transition={{ duration: 0.45, delay: 0.22, ease: "easeOut" }}>
              <ModeBox id="tour-browser-mode" value={headlessMode} onChange={setHeadlessMode} />
              <StepperBox id="tour-mutations" label="Mutations" value={maxMutations} min={1} max={5} onChange={setMaxMutations} />
              <StepperBox id="tour-iterations" label="Iterations" value={maxIterations} min={1} max={15} onChange={setMaxIterations} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── ACTIVE SCAN LAYOUT ── */}
      <AnimatePresence>
        {isScanning && (
          <motion.div
            key="scan-layout"
            className="absolute inset-0 flex flex-col z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.4, delay: 0.3 } }}
            exit={{ opacity: 0, transition: { duration: 0.25 } }}
          >
            {/* ── Top bar: read-only URL + stop button ── */}
            <motion.div
              className="mx-6 mt-5 mb-4 relative group shrink-0"
              initial={{ y: 40, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ type: "spring", stiffness: 200, damping: 26, delay: 0.1 }}
            >
              {/* Pulsing glow */}
              <motion.div
                animate={{ opacity: [0.3, 0.55, 0.3] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -inset-2 bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-xl blur-2xl pointer-events-none z-0" />
              <motion.div
                animate={{ opacity: [0.45, 0.7, 0.45] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -inset-[1px] bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-lg pointer-events-none z-0" />

              <div className="relative z-10 w-full rounded-lg p-1 flex items-center shadow-sm"
                style={{ background: "rgba(16,16,18,0.90)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.08)" }}>
                {/* Scanning pulse dot */}
                <span className="ml-4 mr-3 shrink-0 relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                </span>
                <span className="flex-1 text-zinc-400 text-[15px] truncate py-3.5 select-none">{url}</span>
                <motion.button
                  onClick={handleStop}
                  whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  className="bg-white text-black hover:bg-zinc-100 px-4 py-2 mr-1 rounded-md font-medium transition-colors flex items-center justify-center h-10 w-12">
                  <Square className="w-5 h-5 fill-black border-none" />
                </motion.button>
              </div>
            </motion.div>

            {/* ── Two-panel body ── */}
            <div className="flex flex-1 gap-4 px-6 pb-5 overflow-hidden">

              {/* LEFT — 35% stats */}
              <motion.div
                className="w-[35%] shrink-0 flex flex-col justify-between rounded-xl px-5 py-5"
                style={{ background: "rgba(10,10,12,0.30)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}
                initial={{ x: -24, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ type: "spring", stiffness: 180, damping: 24, delay: 0.25 }}
              >
                <div className="flex flex-col gap-6">
                  {/* Target & Elapsed */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold">Target</span>
                      <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold">Elapsed</span>
                    </div>
                    <div className="flex justify-between items-end">
                      <span className="text-lg font-semibold text-zinc-100 truncate pr-4">{targetName}</span>
                      <motion.span
                        key={elapsedSeconds}
                        initial={{ opacity: 0.6 }} animate={{ opacity: 1 }}
                        transition={{ duration: 0.2 }}
                        className="text-lg font-semibold text-zinc-200 tabular-nums font-mono shrink-0">
                        {formatTime(elapsedSeconds)}
                      </motion.span>
                    </div>
                  </div>

                  <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />

                  {/* Bars */}
                  <div className="flex flex-col gap-5">
                    <StatBar
                      label="Iteration"
                      value={currentIteration}
                      max={maxIterations}
                      display={`${currentIteration} / ${maxIterations}`}
                      color="linear-gradient(to right, rgba(139,92,246,0.7), rgba(168,85,247,0.9))"
                    />
                    <StatBar
                      label="Mutation"
                      value={currentMutation}
                      max={maxMutations}
                      display={`${currentMutation} / ${maxMutations}`}
                      color="linear-gradient(to right, rgba(59,130,246,0.7), rgba(99,102,241,0.9))"
                    />
                  </div>
                </div>

                {/* Big Severity */}
                <div className="mt-6 flex flex-col gap-2">
                  <div className="flex justify-between items-end">
                    <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold">Severity</span>
                    <span className="text-2xl font-bold tabular-nums" style={{ WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundImage: severityColor }}>
                      {currentSeverity}%
                    </span>
                  </div>
                  <div className="relative h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                    <motion.div
                      className="absolute left-0 top-0 h-full rounded-full"
                      style={{ background: severityColor, boxShadow: "0 0 12px " + (currentSeverity > 50 ? "rgba(239,68,68,0.4)" : "transparent") }}
                      animate={{ width: `${currentSeverity}%` }}
                      transition={{ type: "spring", stiffness: 120, damping: 20 }}
                    />
                  </div>
                </div>
              </motion.div>

              {/* RIGHT — 65% logs */}
              <motion.div
                className="flex-1 flex flex-col rounded-xl overflow-hidden"
                style={{ background: "rgba(10,10,12,0.30)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}
                initial={{ x: 24, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ type: "spring", stiffness: 180, damping: 24, delay: 0.3 }}
              >
                {/* Log header */}
                <div className="px-4 py-2.5 flex items-center gap-2 shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                  <span className="text-[9px] uppercase tracking-widest text-zinc-600 font-semibold">Live Output</span>
                  <div className="ml-auto flex items-center gap-1.5">
                    <span className="animate-pulse w-1.5 h-1.5 rounded-full bg-red-500/80" />
                    <span className="text-[9px] text-zinc-600 uppercase tracking-wider">Streaming</span>
                  </div>
                </div>

                {/* Log body */}
                <div className="flex-1 overflow-y-auto px-4 py-3 font-mono text-[11px] leading-5 space-y-0.5 no-scrollbar">
                  <AnimatePresence initial={false}>
                    {logLines.map((line, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: 6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.2 }}
                        className={`whitespace-pre-wrap break-all ${logLineStyle(line)}`}
                      >
                        {line}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  <div ref={logEndRef} />
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
