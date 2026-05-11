"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
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
        // In local dev without email setup, it auto-logs in.
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
    } catch (err: any) {
      setError(err.message || "An error occurred");
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
      <div className="h-screen w-screen bg-zinc-950 flex items-center justify-center font-sans text-zinc-300">
        <div className="w-full max-w-sm p-8 bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl">
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
                className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-200 outline-none focus:border-zinc-500 transition-colors"
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
                className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-200 outline-none focus:border-zinc-500 transition-colors"
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
