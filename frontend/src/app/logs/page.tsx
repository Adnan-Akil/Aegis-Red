"use client";

import { useEffect, useState } from "react";
import { Download, Loader2, ScrollText, Zap, Fingerprint, Activity, Terminal, Trash2, AlertTriangle } from "lucide-react";
import { supabase } from "@/lib/supabase";

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);

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

  const handleClearAll = async () => {
    setClearing(true);
    setClearError(null);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // Step 1: Fetch the exact IDs to delete (scoped to this user)
      const { data: rows, error: fetchError } = await supabase
        .from("attack_sessions")
        .select("id")
        .eq("user_id", user.id);

      if (fetchError) throw fetchError;
      if (!rows || rows.length === 0) { setLogs([]); setShowConfirm(false); return; }

      const ids = rows.map((r) => r.id);

      // Step 2: Delete by primary key
      const { error: deleteError } = await supabase
        .from("attack_sessions")
        .delete()
        .in("id", ids);

      if (deleteError) throw deleteError;

      // Step 3: Verify the rows are actually gone — don't trust !error alone (RLS can silently block)
      const { count, error: verifyError } = await supabase
        .from("attack_sessions")
        .select("*", { count: "exact", head: true })
        .eq("user_id", user.id);

      if (verifyError) throw verifyError;

      if (count === 0) {
        setLogs([]);
        setShowConfirm(false);
      } else {
        // Delete was silently blocked (RLS policy missing for DELETE)
        setClearError(
          `Delete was blocked by Supabase RLS. ${count} record(s) still exist. ` +
          `Go to Supabase Dashboard → Table Editor → attack_sessions → RLS Policies ` +
          `and add a DELETE policy: USING (auth.uid() = user_id)`
        );
      }
    } catch (err: any) {
      console.error("Clear error", err);
      setClearError(err?.message || "An unexpected error occurred.");
    } finally {
      setClearing(false);
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

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-md rounded-2xl border border-red-500/20 bg-zinc-950 p-8 shadow-2xl">
            <div className="mb-6 flex flex-col items-center gap-4 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full border border-red-500/30 bg-red-500/10">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold tracking-tight text-white">Purge All Logs?</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-500">
                  This will permanently delete <span className="font-mono text-zinc-300">{logs.length}</span> session{logs.length !== 1 ? "s" : ""} from the database. This action{" "}
                  <span className="font-semibold text-red-400">cannot be undone</span>.
                </p>
              </div>
            </div>
            {clearError && (
              <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3">
                <p className="text-xs leading-relaxed text-red-400">{clearError}</p>
              </div>
            )}
            <div className="flex gap-3">
              <button
                onClick={() => { setShowConfirm(false); setClearError(null); }}
                className="flex-1 rounded-xl border border-zinc-800 bg-zinc-900 py-2.5 text-sm font-medium text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleClearAll}
                disabled={clearing}
                className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 py-2.5 text-sm font-semibold text-red-400 transition-colors hover:bg-red-500/20 hover:text-red-300 disabled:opacity-50"
              >
                {clearing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                {clearing ? "Purging..." : "Confirm Purge"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="shrink-0 px-8 pt-0 pb-6">
        <h2 className="text-3xl font-semibold tracking-tight text-white">System Logs</h2>
        <p className="text-sm uppercase tracking-wide text-zinc-500">Real-time execution tracing</p>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden px-8 pb-6 no-scrollbar">
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

      {/* Clear All Button — centered at the bottom */}
      {logs.length > 0 && (
        <div className="shrink-0 flex justify-center py-8 px-8">
          <button
            id="clear-all-logs-btn"
            onClick={() => setShowConfirm(true)}
            className="flex items-center gap-2.5 rounded-xl border border-red-500/20 bg-red-500/5 px-6 py-3 font-mono text-xs font-semibold uppercase tracking-widest text-red-500/70 transition-all duration-200 hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-400"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Purge All Logs
          </button>
        </div>
      )}
    </div>
  );
}
