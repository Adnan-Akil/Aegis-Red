"use client";

import { useState, useEffect, useLayoutEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { X, ArrowRight, ArrowLeft } from "lucide-react";
import { supabase } from "@/lib/supabase";

// ─── Tour Steps Definition ────────────────────────────────────────────────────
const TOUR_KEY_PREFIX = "aegis_tour_done_v1";
function tourKey(userId: string) { return `${TOUR_KEY_PREFIX}_${userId}`; }

interface TourStep {
  targetId: string;
  title: string;
  description: string;
  placement: "top" | "bottom" | "right" | "left";
  padding?: number;
  tooltipOffset?: number; // extra gap beyond GAP for steps that need more clearance
}

const STEPS: TourStep[] = [
  {
    targetId: "tour-url-input",
    title: "Target URL",
    description: "Paste the URL of any AI chatbot you want to audit. Aegis-Red will automatically probe, attack, and evaluate it.",
    placement: "bottom",
    padding: 8,
  },
  {
    targetId: "tour-launch-btn",
    title: "Launch Attack",
    description: "Hit this to fire the attack sequence. Once a scan is running, this button becomes a kill switch to abort immediately.",
    placement: "left",
    padding: 8,
  },
  {
    targetId: "tour-browser-mode",
    title: "Browser Mode",
    description: "Scroll or click to switch between Headless (invisible) and Headed (visible browser window). Use Headed to debug; Headless for production runs.",
    placement: "top",
    padding: 8,
    tooltipOffset: 24,
  },
  {
    targetId: "tour-mutations",
    title: "Mutations",
    description: "Controls how many payload variants the Mutator generates per attack iteration. Higher values = more creative, harder-to-detect attacks.",
    placement: "top",
    padding: 8,
    tooltipOffset: 24,
  },
  {
    targetId: "tour-iterations",
    title: "Iterations",
    description: "The number of full attack-evaluate cycles the agent runs. More iterations = deeper persistence and adaptive strategy shifts.",
    placement: "top",
    padding: 8,
    tooltipOffset: 24,
  },
  {
    targetId: "tour-nav-reports",
    title: "Audit Reports",
    description: "All completed scan results live here. Each report is a full AI-generated penetration test document with findings and remediation steps.",
    placement: "right",
    padding: 8,
  },
  {
    targetId: "tour-nav-logs",
    title: "Execution Logs",
    description: "Raw attack traces from every scan run — every payload sent, every response received, and every evaluation verdict.",
    placement: "right",
    padding: 8,
  },
  {
    targetId: "tour-profile-btn",
    title: "Your Profile",
    description: "Manage your account credentials here. You can update your username, email, and password, or sign out.",
    placement: "right",
    padding: 8,
  },
];

// ─── Rect helper ──────────────────────────────────────────────────────────────
function getRect(id: string): DOMRect | null {
  const el = document.getElementById(id);
  return el ? el.getBoundingClientRect() : null;
}

// ─── Tooltip positioning ──────────────────────────────────────────────────────
const TOOLTIP_W = 320;
const TOOLTIP_H = 160; // approx
const GAP = 16;

function calcTooltipPos(
  rect: DOMRect,
  placement: TourStep["placement"],
  extraOffset = 0,
): { top: number; left: number } {
  const gap = GAP + extraOffset;
  switch (placement) {
    case "bottom":
      return {
        top: rect.bottom + gap,
        left: rect.left + rect.width / 2 - TOOLTIP_W / 2,
      };
    case "top":
      return {
        top: rect.top - TOOLTIP_H - gap,
        left: rect.left + rect.width / 2 - TOOLTIP_W / 2,
      };
    case "right":
      return {
        top: rect.top + rect.height / 2 - TOOLTIP_H / 2,
        left: rect.right + gap,
      };
    case "left":
      return {
        top: rect.top + rect.height / 2 - TOOLTIP_H / 2,
        left: rect.left - TOOLTIP_W - gap,
      };
  }
}

// ─── Main Component ───────────────────────────────────────────────────────────
interface IntroTourProps {
  onDone: () => void;
  userId: string;
}

export function IntroTour({ onDone, userId }: IntroTourProps) {
  const [step, setStep] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [mounted, setMounted] = useState(false);
  const padding = STEPS[step].padding ?? 8;

  // Mount guard for SSR
  useEffect(() => { setMounted(true); }, []);

  // Recompute rect whenever step changes or window resizes
  // Must run inside rAF so it fires AFTER Framer Motion applies its transforms
  const updateRect = () => {
    requestAnimationFrame(() => {
      const r = getRect(STEPS[step].targetId);
      setRect(r);
      if (r) {
        document.getElementById(STEPS[step].targetId)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    });
  };

  useLayoutEffect(() => {
    updateRect();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, mounted]);

  useEffect(() => {
    window.addEventListener("resize", updateRect);
    return () => window.removeEventListener("resize", updateRect);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const handleNext = () => {
    if (step < STEPS.length - 1) setStep(s => s + 1);
    else handleDone();
  };

  const handleBack = () => {
    if (step > 0) setStep(s => s - 1);
  };

  const handleDone = () => {
    localStorage.setItem(tourKey(userId), "1");
    onDone();
  };

  if (!mounted) return null;

  const currentStep = STEPS[step];
  const tooltipPos = rect
    ? calcTooltipPos(rect, currentStep.placement, currentStep.tooltipOffset ?? 0)
    : { top: 0, left: 0 };

  // Smart clamp: keep tooltip within viewport, flipping if needed
  const vw = typeof window !== "undefined" ? window.innerWidth : 1280;
  const vh = typeof window !== "undefined" ? window.innerHeight : 800;
  // Clamp horizontal
  tooltipPos.left = Math.max(12, Math.min(tooltipPos.left, vw - TOOLTIP_W - 12));
  // Clamp vertical: if overflows bottom, flip it above the spotlight instead
  if (tooltipPos.top + TOOLTIP_H + 12 > vh && rect) {
    tooltipPos.top = rect.top - TOOLTIP_H - (GAP + (currentStep.tooltipOffset ?? 0));
  }
  // Final safety clamp — never go above viewport top
  tooltipPos.top = Math.max(12, tooltipPos.top);

  const spotlight = rect
    ? {
        top: rect.top - padding,
        left: rect.left - padding,
        width: rect.width + padding * 2,
        height: rect.height + padding * 2,
      }
    : null;

  return createPortal(
    <AnimatePresence>
      <div className="fixed inset-0 z-[9999] pointer-events-none">
        {/* Dark overlay with spotlight cut-out */}
        {spotlight && (
          <motion.div
            key={`overlay-${step}`}
            className="absolute inset-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{
              pointerEvents: "auto",
              background: "rgba(0,0,0,0.72)",
              WebkitMaskImage: `radial-gradient(
                ellipse at ${spotlight.left + spotlight.width / 2}px ${spotlight.top + spotlight.height / 2}px,
                transparent ${Math.max(spotlight.width, spotlight.height) * 0.42}px,
                black ${Math.max(spotlight.width, spotlight.height) * 0.58}px
              )`,
              maskImage: `radial-gradient(
                ellipse at ${spotlight.left + spotlight.width / 2}px ${spotlight.top + spotlight.height / 2}px,
                transparent ${Math.max(spotlight.width, spotlight.height) * 0.42}px,
                black ${Math.max(spotlight.width, spotlight.height) * 0.58}px
              )`,
            }}
            onClick={handleDone}
          />
        )}

        {/* Spotlight ring */}
        {spotlight && (
          <motion.div
            key={`ring-${step}`}
            className="absolute rounded-xl pointer-events-none"
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 280, damping: 24 }}
            style={{
              top: spotlight.top,
              left: spotlight.left,
              width: spotlight.width,
              height: spotlight.height,
              boxShadow: "0 0 0 2px rgba(220,38,38,0.7), 0 0 28px 4px rgba(220,38,38,0.18)",
            }}
          />
        )}

        {/* Tooltip card */}
        <motion.div
          key={`tooltip-${step}`}
          className="absolute pointer-events-auto"
          style={{
            top: tooltipPos.top,
            left: tooltipPos.left,
            width: TOOLTIP_W,
            zIndex: 10000,
          }}
          initial={{ opacity: 0, y: 8, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 4 }}
          transition={{ type: "spring", stiffness: 320, damping: 28, delay: 0.06 }}
        >
          <div
            className="rounded-xl p-4 flex flex-col gap-3"
            style={{
              background: "rgba(14,14,16,0.92)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(255,255,255,0.1)",
              boxShadow: "0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(220,38,38,0.12)",
            }}
          >
            {/* Header row */}
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="text-[9px] uppercase tracking-widest text-red-500/80 font-semibold">
                  Step {step + 1} of {STEPS.length}
                </span>
                <h3 className="text-sm font-semibold text-white mt-0.5">{currentStep.title}</h3>
              </div>
              <button
                onClick={handleDone}
                className="text-zinc-600 hover:text-zinc-300 transition-colors shrink-0 mt-0.5"
                aria-label="Close tour"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Description */}
            <p className="text-[12.5px] text-zinc-400 leading-relaxed">{currentStep.description}</p>

            {/* Progress dots */}
            <div className="flex items-center gap-1.5">
              {STEPS.map((_, i) => (
                <div
                  key={i}
                  className="rounded-full transition-all duration-300"
                  style={{
                    width: i === step ? 16 : 5,
                    height: 4,
                    background: i === step ? "#dc2626" : "rgba(255,255,255,0.15)",
                  }}
                />
              ))}
            </div>

            {/* Nav buttons */}
            <div className="flex items-center justify-between pt-1">
              <button
                onClick={handleBack}
                disabled={step === 0}
                className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ArrowLeft className="w-3 h-3" /> Back
              </button>
              <button
                onClick={handleNext}
                className="flex items-center gap-1.5 text-xs font-medium text-white bg-red-600/80 hover:bg-red-600 px-3 py-1.5 rounded-md transition-colors"
              >
                {step === STEPS.length - 1 ? "Finish" : "Next"}
                {step < STEPS.length - 1 && <ArrowRight className="w-3 h-3" />}
              </button>
            </div>
          </div>
        </motion.div>

        {/* Skip button — bottom right, prominent red */}
        <button
          className="fixed bottom-6 right-6 flex items-center gap-1.5 text-xs font-semibold text-white bg-red-600/90 hover:bg-red-600 px-4 py-2 rounded-lg transition-all duration-200 pointer-events-auto shadow-lg shadow-red-900/30"
          onClick={handleDone}
        >
          <X className="w-3 h-3" />
          Skip tour
        </button>
      </div>
    </AnimatePresence>,
    document.body
  );
}

// ─── Hook for triggering the tour ────────────────────────────────────────────
export function useTour() {
  const [showTour, setShowTour] = useState(false);
  const [userId, setUserId] = useState("");

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) return;
      setUserId(user.id);
      const done = localStorage.getItem(tourKey(user.id));
      if (!done) {
        // Small delay so DOM elements with IDs are fully rendered
        const t = setTimeout(() => setShowTour(true), 800);
        return () => clearTimeout(t);
      }
    });
  }, []);

  return { showTour, userId, closeTour: () => setShowTour(false) };
}
