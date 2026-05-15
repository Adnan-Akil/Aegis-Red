"use client";

import { useEffect, useState } from "react";
import { Download, Loader2, ScrollText, Zap, Fingerprint, Activity, Terminal } from "lucide-react";
import { supabase } from "@/lib/supabase";

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const { data, error } = await supabase
          .from("attack_sessions")
          .select("*")
          .eq("user_id", user.id)
          .order("created_at", { ascending: false });

        if (!error && data) setLogs(data);
      } catch (err) {
        console.error("Fetch failed", err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const handleDownload = async (path: string) => {
    if (!path) return;
    try {
      const { data } = await supabase.storage.from("attack-artifacts").createSignedUrl(path, 60);
      if (data?.signedUrl) {
        const response = await fetch(data.signedUrl);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = path.split("/").pop() || "trace.md";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error("Download failed", err);
    }
  };

  const getLogType = (status: string, verdict: string) => {
    if (status === "running") return "action";
    const v = (verdict || "").toLowerCase();
    if (v.includes("critical") || v.includes("compromised")) return "critical";
    if (v.includes("warning")) return "warning";
    return "info";
  };

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#0a0a0a]">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-600" />
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col bg-transparent font-['Elms_Sans']">
      <div className="shrink-0 px-8 pt-0 pb-6">
        <h2 className="text-3xl font-semibold tracking-tight text-white">System Logs</h2>
        <p className="text-sm uppercase tracking-wide text-zinc-500">Real-time execution tracing</p>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden px-8 pb-20 no-scrollbar">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-800/50 bg-zinc-950/20 py-20">
            <ScrollText className="mb-4 h-12 w-12 text-zinc-700" />
            <p className="text-base font-medium text-zinc-500">No logs recorded yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {logs.map((log, idx) => {
              const type = getLogType(log.status, log.verdict);
              const displayId = logs.length - idx;
              const dateObj = new Date(log.created_at);
              const dateStr = dateObj.toLocaleDateString();
              const timeStr = dateObj.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

              return (
                <div
                  key={log.id}
                  className="group relative flex min-h-[240px] flex-col rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-6 transition-all duration-300 hover:border-zinc-600 hover:bg-zinc-900/50"
                >
                  <div className="mb-4 flex items-start justify-between">
                    <div className="font-mono text-[10px] tracking-widest text-zinc-500">
                      #{displayId < 10 ? `0${displayId}` : displayId} | {dateStr} | {timeStr}
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDownload(log.payload_file_url); }}
                      className="rounded-lg border border-zinc-800 bg-zinc-800/50 p-2 text-zinc-500 transition-colors hover:bg-zinc-700 hover:text-white disabled:opacity-30"
                      disabled={!log.payload_file_url}
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  </div>

                  <h3 className="mb-3 truncate text-sm font-bold tracking-tight text-white" title={log.target_url}>
                    {log.target_url}
                  </h3>

                  <div className="mb-4 flex flex-wrap gap-2">
                    {type === "critical" && (
                      <span className="flex items-center gap-1.5 rounded border border-red-500/30 bg-red-500/10 px-2 py-1 text-[10px] font-bold text-red-400">
                        <Zap className="h-3 w-3" /> COMPROMISED
                      </span>
                    )}
                    {type === "info" && (
                      <span className="flex items-center gap-1.5 rounded border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-[10px] font-bold text-cyan-400">
                        <Fingerprint className="h-3 w-3" /> SECURE
                      </span>
                    )}
                    {type === "action" && (
                      <span className="flex items-center gap-1.5 rounded border border-purple-500/30 bg-purple-500/10 px-2 py-1 text-[10px] font-bold text-purple-400">
                        <Terminal className="h-3 w-3" /> ACTIVE_RUN
                      </span>
                    )}
                    {type === "warning" && (
                      <span className="flex items-center gap-1.5 rounded border border-yellow-500/30 bg-yellow-500/10 px-2 py-1 text-[10px] font-bold text-yellow-400">
                        <Activity className="h-3 w-3" /> WARNING
                      </span>
                    )}
                  </div>

                  <div className="mt-auto border-t border-zinc-800/50 pt-4">
                    <p className="line-clamp-2 text-xs leading-relaxed text-zinc-400">
                      {log.status === "running" ? "Autonomous agent is navigating target..." : `Session ended. Status: ${log.verdict || "Completed"}`}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
