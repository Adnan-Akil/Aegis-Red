"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { motion } from "framer-motion";
import type { User } from "@supabase/supabase-js";
import { Loader2 } from "lucide-react";
import { useAppContext } from "@/app/context";

export function AuthWrapper({ children }: { children: React.ReactNode }) {
  const { setIsScanning, setStatusText, setScanUrl } = useAppContext();
  
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  useEffect(() => {
    const enforceSecurityPolicy = async () => {
      // Force logout on hard refresh (F5) or manual URL reload
      if (typeof window !== "undefined") {
        const navEntries = window.performance.getEntriesByType("navigation");
        if (navEntries.length > 0 && (navEntries[0] as PerformanceNavigationTiming).type === "reload") {
          await supabase.auth.signOut();
        }
      }

      // Check active session
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      setLoading(false);
    };

    enforceSecurityPolicy();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (!session) {
        setIsScanning(false);
        setStatusText("");
        setScanUrl("");
        setEmail("");
        setPassword("");
      }
    });

    return () => subscription.unsubscribe();
  }, [setIsScanning, setStatusText, setScanUrl]);

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
    } catch (err: any) {
      // Log the real error server-side only — never expose raw Supabase internals to the UI
      console.error("[Auth]", err?.message);

      // Map to safe, generic user-facing messages
      const msg: string = err?.message?.toLowerCase() ?? "";
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

  if (loading) {
    return (
      <div className="h-screen w-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="h-screen w-screen bg-zinc-950 flex items-center justify-center font-sans text-zinc-300 relative overflow-hidden">
        {/* ── Global Background Image ── */}
        <div
          className="fixed inset-0 z-0 pointer-events-none"
          style={{
            backgroundImage: "url('/bg_picture.jpg')",
            backgroundSize: "cover",
            backgroundPosition: "center",
            filter: "blur(5px) brightness(0.52) saturate(0.85)",
            transform: "scale(1.05)",
          }}
        />
        <div className="fixed inset-0 z-0 pointer-events-none bg-black/40" />

        {/* Ambient orbs */}
        <motion.div className="absolute pointer-events-none rounded-full z-0"
          style={{ width: 440, height: 440, background: "radial-gradient(circle, rgba(220,38,38,0.055) 0%, transparent 70%)", top: "18%", left: "12%" }}
          animate={{ x: [0, 20, -12, 0], y: [0, -16, 14, 0] }}
          transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }} />
        <motion.div className="absolute pointer-events-none rounded-full z-0"
          style={{ width: 340, height: 340, background: "radial-gradient(circle, rgba(168,85,247,0.05) 0%, transparent 70%)", bottom: "20%", right: "14%" }}
          animate={{ x: [0, -16, 10, 0], y: [0, 14, -18, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 2 }} />

        {/* Vignette */}
        <div className="absolute inset-0 pointer-events-none z-0" style={{ background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.62) 100%)" }} />

        {/* Glassy authentication card container */}
        <div 
          className="w-full max-w-sm p-8 rounded-2xl shadow-2xl relative z-10"
          style={{ 
            background: "rgba(10,10,12,0.6)", 
            backdropFilter: "blur(12px)", 
            WebkitBackdropFilter: "blur(12px)",
            border: "1px solid rgba(255,255,255,0.04)" 
          }}
        >
          <h1 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: 'var(--font-chaste)' }}>Aegis-Red</h1>
          <p className="text-sm text-zinc-500 mb-8">Authenticate to access the dashboard.</p>
          
          <form onSubmit={handleAuth} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Email</label>
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-black/40 border border-white/5 rounded-lg px-4 py-2.5 text-sm text-zinc-200 outline-none focus:border-white/20 transition-colors"
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
                className="bg-black/40 border border-white/5 rounded-lg px-4 py-2.5 text-sm text-zinc-200 outline-none focus:border-white/20 transition-colors"
                placeholder="••••••••"
              />
            </div>
            
            {error && (
              <div className="text-red-400 text-xs bg-red-500/10 p-2 rounded border border-red-500/20">
                {error}
              </div>
            )}

            <button 
              type="submit" 
              disabled={authLoading}
              className="mt-2 w-full bg-zinc-200 text-black hover:bg-white transition-colors font-medium py-2.5 rounded-lg text-sm flex items-center justify-center disabled:opacity-50"
            >
              {authLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (isSignUp ? "Sign Up" : "Sign In")}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button 
              onClick={() => setIsSignUp(!isSignUp)}
              className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              {isSignUp ? "Already have an account? Sign In" : "Need an account? Sign Up"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Once authenticated, render children (AppShell)
  return <>{children}</>;
}
