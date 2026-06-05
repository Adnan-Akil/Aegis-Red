"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Loader2, Square } from "lucide-react";
import { useAppContext } from "@/app/context";
import { supabase } from "@/lib/supabase";

export default function LandingPage() {
  const { 
    userName,
    headlessMode, maxMutations, maxIterations,
    isScanning, setIsScanning,
    statusText, setStatusText,
    scanUrl: url, setScanUrl: setUrl
  } = useAppContext();

  const abortControllerRef = useRef<AbortController | null>(null);
  const scanStartTimeRef = useRef<number>(0);

  const handleStop = () => {
    // Prevent accidental double-click from immediately stopping the attack
    if (Date.now() - scanStartTimeRef.current < 500) return;
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    if (isScanning) {
      handleStop();
      return;
    }

    setIsScanning(true);
    setStatusText("Initializing attack sequence...");
    abortControllerRef.current = new AbortController();
    scanStartTimeRef.current = Date.now();

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("No authenticated user found");

      const response = await fetch("/api/run", {
        method: "POST",
        signal: abortControllerRef.current.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url.trim(),
          headless: headlessMode,
          mutations: maxMutations,
          iterations: maxIterations,
          user_id: user.id
        }),
      });

      if (!response.ok) throw new Error("Failed to start agent");
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        let partialData = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          partialData += chunk;
          
          const lines = partialData.split("\n");
          partialData = lines.pop() || ""; 
          
          for (const line of lines) {
            let nextStatus = "";
            if (line.includes("Active Prober")) nextStatus = "Active Prober: Interrogating target...";
            else if (line.includes("[Iteration")) {
              const match = line.match(/\[Iteration (\d+)\]/);
              if (match) nextStatus = `Iteration ${match[1]}: Planning attack...`;
            }
            else if (line.includes("🗡️ Attack:")) {
              const match = line.match(/🗡️ Attack: ([^ (]+)/);
              if (match) nextStatus = `Executing: ${match[1].toLowerCase()} attack...`;
            }
            else if (line.includes("Verdict:")) nextStatus = "Evaluating target response...";
            else if (line.includes("Session Complete")) nextStatus = "Attack session complete.";

            if (nextStatus) {
              setStatusText(nextStatus);
              // Give React time to render the fade animation if multiple statuses arrive at once
              await new Promise(resolve => setTimeout(resolve, 400));
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === "AbortError") {
        setStatusText("Attack sequence aborted by user.");
      } else {
        console.error(error);
        setStatusText(`Error: ${error.message}`);
      }
    } finally {
      setIsScanning(false);
      setTimeout(() => setStatusText(""), 5000);
      setUrl("");
    }
  };

  return (
    <div className="h-full w-full flex flex-col items-center justify-center px-6 pb-24 relative overflow-hidden">

      {/* Background Layer 1: dot grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.055) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />

      {/* Background Layer 3: vignette edges */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55) 100%)",
        }}
      />

      <div className="relative z-10 w-full max-w-2xl flex flex-col">

        <div className="mb-3 text-left pl-1">
          <h2 className="text-3xl font-medium text-white mb-1">Good evening, {userName}.</h2>
          <p className="text-zinc-500 text-sm">What are we testing today?</p>
        </div>

        <div className="relative w-full group">
          {/* Static/Focus Gradient Glows (Active when not scanning) */}
          {!isScanning && (
            <>
              {/* Outer Ambient Glow - Wide & Blurred */}
              <div className="absolute -inset-4 bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-xl blur-3xl opacity-20 group-focus-within:opacity-45 transition-opacity duration-500 pointer-events-none z-0" />
              {/* Medium Blurred Glow */}
              <div className="absolute -inset-1.5 bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-lg blur-xl opacity-35 group-focus-within:opacity-60 transition-opacity duration-500 pointer-events-none z-0" />
              {/* Tight Border Glow - Crisp Edge */}
              <div className="absolute -inset-[1px] bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-lg opacity-60 group-focus-within:opacity-85 transition-opacity duration-500 pointer-events-none z-0" />
            </>
          )}

          {/* Scanning Dynamic/Pulsing Gradient Glows */}
          <AnimatePresence>
            {isScanning && (
              <>
                {/* Scanning Outer Ambient Glow */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 0.45, scale: 1.05 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 2, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
                  className="absolute -inset-4 bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-xl blur-3xl z-0 pointer-events-none"
                />
                {/* Scanning Medium Blurred Glow */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 0.65, scale: 1.02 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 1.5, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
                  className="absolute -inset-1.5 bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-lg blur-xl z-0 pointer-events-none"
                />
                {/* Scanning Sharp Edge Glow */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.9 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="absolute -inset-[1px] bg-gradient-to-r from-red-600 via-purple-600 to-rose-500 rounded-lg z-0 pointer-events-none"
                />
              </>
            )}
          </AnimatePresence>
          
          <form
            onSubmit={handleScan}
            className="relative z-10 w-full bg-[#18181b] border border-zinc-800 rounded-lg p-1 flex items-center transition-colors focus-within:border-zinc-600 shadow-sm"
          >
            <input
              type="url"
              placeholder="Enter target AI URL..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={isScanning}
              required
              className="flex-1 bg-transparent border-none outline-none text-zinc-200 placeholder-zinc-600 px-4 py-3 disabled:opacity-50"
            />
            <button
              type={isScanning ? "button" : "submit"}
              onClick={isScanning ? handleStop : undefined}
              disabled={!isScanning && !url}
              className="bg-white text-black hover:bg-zinc-200 px-4 py-2 mr-1 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center h-10 w-12"
            >
              {isScanning ? (
                <Square className="w-5 h-5 fill-black border-none" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </button>
          </form>
        </div>

        <div className="h-6 mt-4 flex items-center pl-2 overflow-hidden">
          <AnimatePresence mode="wait">
            {statusText && (
              <motion.div 
                key={statusText}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="text-zinc-500 text-xs tracking-wide"
              >
                {statusText}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
