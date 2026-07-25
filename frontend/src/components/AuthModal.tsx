"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, X } from "lucide-react";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultMode?: "signin" | "signup";
}

export function AuthModal({ isOpen, onClose, defaultMode = "signin" }: AuthModalProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(defaultMode === "signup");
  const [error, setError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setError("");
    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
      onClose();
    } catch (err: unknown) {
      console.error("[Auth]", (err as Error)?.message);
      const msg = (err as Error)?.message?.toLowerCase() ?? "";
      if (msg.includes("invalid login") || msg.includes("invalid credentials") || msg.includes("wrong password")) {
        setError("Invalid email or password.");
      } else if (msg.includes("email not confirmed")) {
        setError("Please confirm your email address before signing in.");
      } else if (msg.includes("rate limit") || msg.includes("too many")) {
        setError("Too many attempts. Please wait a moment and try again.");
      } else if (msg.includes("user already registered") || msg.includes("already been registered")) {
        setError("An account with this email already exists. Try signing in.");
      } else if (msg.includes("password") && msg.includes("short")) {
        setError("Password must be at least 6 characters.");
      } else {
        setError("Authentication failed. Please check your credentials and try again.");
      }
    } finally {
      setAuthLoading(false);
    }
  };

  const switchMode = () => {
    setIsSignUp((prev) => !prev);
    setError("");
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/60 cursor-pointer"
            style={{ backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }}
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Card */}
          <motion.div
            className="relative z-10 w-full max-w-sm mx-4 p-8 rounded-2xl shadow-2xl"
            style={{
              background: "rgba(14, 14, 16, 0.72)",
              backdropFilter: "blur(28px)",
              WebkitBackdropFilter: "blur(28px)",
              border: "1px solid rgba(255,255,255,0.09)",
              boxShadow: "0 32px 80px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.06)",
            }}
            initial={{ opacity: 0, y: 28, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 18, scale: 0.97 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-zinc-600 hover:text-zinc-300 transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Header */}
            <div className="text-center mb-7">
              <h2
                className="text-2xl font-bold text-white mb-1.5 tracking-widest"
                style={{ fontFamily: "var(--font-chaste)" }}
              >
                Aegis-Red
              </h2>
              <p className="text-xs text-zinc-500">
                {isSignUp ? "Create your operator account." : "Authenticate to access the dashboard."}
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleAuth} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-black/20 border border-white/5 rounded-lg px-4 py-2.5 text-sm text-zinc-200 outline-none focus:border-white/20 transition-colors backdrop-blur-sm"
                  placeholder="operator@aegis-red.dev"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-black/20 border border-white/5 rounded-lg px-4 py-2.5 text-sm text-zinc-200 outline-none focus:border-white/20 transition-colors backdrop-blur-sm"
                  placeholder="••••••••"
                />
              </div>

              <div className="flex items-start gap-2 mt-1">
                <input
                  type="checkbox"
                  id="auth-disclaimer"
                  required
                  className="mt-0.5 rounded bg-black/40 border-white/10 text-red-500 focus:ring-red-500/20 cursor-pointer"
                />
                <label htmlFor="auth-disclaimer" className="text-[11px] text-zinc-400 leading-tight cursor-pointer">
                  I confirm I have explicit legal authorization to perform red-teaming security assessments on target systems per our{" "}
                  <a href="/terms" target="_blank" className="text-zinc-200 underline hover:text-white">Terms</a> and{" "}
                  <a href="/privacy" target="_blank" className="text-zinc-200 underline hover:text-white">Privacy Policy</a>.
                </label>
              </div>

              {error && (
                <div className="text-red-400 text-xs bg-red-500/10 p-2 rounded border border-red-500/20">
                  {error}
                </div>
              )}

              <motion.button
                type="submit"
                whileTap={{ scale: 0.96 }}
                disabled={authLoading}
                className="mt-2 w-full bg-zinc-200 text-black hover:bg-white transition-colors font-medium py-2.5 rounded-lg text-sm flex items-center justify-center disabled:opacity-50 cursor-pointer"
              >
                {authLoading
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : (isSignUp ? "Sign Up" : "Sign In")}
              </motion.button>
            </form>

            <div className="mt-5 text-center">
              <button
                onClick={switchMode}
                className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
              >
                {isSignUp
                  ? "Already have an account? Sign In"
                  : "Need an account? Sign Up"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
