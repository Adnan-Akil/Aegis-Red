"use client";

import { useEffect, useState } from "react";
import { Download, Loader2, ShieldCheck, Zap, Fingerprint, Activity, Terminal, Trash2, AlertTriangle, Search, FileText } from "lucide-react";
import { supabase } from "@/lib/supabase";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getStatusType(status: string, verdict: string) {
  if (status === "running") return "action";
  const v = (verdict || "").toLowerCase();
  if (v.includes("critical") || v.includes("compromised")) return "critical";
  if (v.includes("warning")) return "warning";
  return "info";
}

export default function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Selection & Content
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [markdownContent, setMarkdownContent] = useState<string>("");
  const [markdownLoading, setMarkdownLoading] = useState(false);
  
  // Search & Filters
  const [searchQuery, setSearchQuery] = useState("");

  // Purge State
  const [showConfirm, setShowConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const { data, error } = await supabase
          .from("attack_sessions")
          .select("*")
          .eq("user_id", user.id)
          .order("created_at", { ascending: false });

        if (!error && data) {
          setReports(data);
          if (data.length > 0) setSelectedReport(data[0]);
        }
      } catch (err) {
        console.error("Fetch failed", err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  // Fetch markdown when selected report changes
  useEffect(() => {
    if (!selectedReport) return;
    
    const fetchMd = async () => {
      setMarkdownLoading(true);
      if (!selectedReport.report_file_url) {
        setMarkdownContent("### No Formal Report Generated\nThis session either failed or was aborted before a formal report could be compiled.");
        setMarkdownLoading(false);
        return;
      }
      try {
        const { data } = await supabase.storage.from("attack-artifacts").createSignedUrl(selectedReport.report_file_url, 60);
        if (data?.signedUrl) {
          const res = await fetch(data.signedUrl);
          const text = await res.text();
          // Preprocess markdown to ensure tables have blank lines around them
          const fixedText = text
            .replace(/([^\n|])\n(\s*\|)/g, '$1\n\n$2') 
            .replace(/(\|\s*)\n([^\n|])/g, '$1\n\n$2');
          setMarkdownContent(fixedText);
        } else {
          setMarkdownContent("Failed to generate secure URL for report.");
        }
      } catch (err) {
        setMarkdownContent("Failed to load report content from storage.");
      } finally {
        setMarkdownLoading(false);
      }
    };
    fetchMd();
  }, [selectedReport]);

  const handleDownload = async (path: string, defaultName: string) => {
    if (!path) return;
    try {
      const { data } = await supabase.storage.from("attack-artifacts").createSignedUrl(path, 60);
      if (data?.signedUrl) {
        const response = await fetch(data.signedUrl);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        // Sanitise filename: take only the basename, strip any path traversal characters
        const rawName = path.split("/").pop() || defaultName;
        a.download = rawName.replace(/[^a-zA-Z0-9._\-]/g, "_");
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

      const { data: rows, error: fetchError } = await supabase.from("attack_sessions").select("id").eq("user_id", user.id);
      if (fetchError) throw fetchError;
      if (!rows || rows.length === 0) { setReports([]); setShowConfirm(false); return; }

      const ids = rows.map((r) => r.id);
      const { error: deleteError } = await supabase.from("attack_sessions").delete().in("id", ids);
      if (deleteError) throw deleteError;

      const { count, error: verifyError } = await supabase.from("attack_sessions").select("*", { count: "exact", head: true }).eq("user_id", user.id);
      if (verifyError) throw verifyError;

      if (count === 0) {
        setReports([]);
        setSelectedReport(null);
        setMarkdownContent("");
        setShowConfirm(false);
      } else {
        setClearError("Delete was blocked by Supabase RLS.");
      }
    } catch (err: any) {
      setClearError(err?.message || "An unexpected error occurred.");
    } finally {
      setClearing(false);
    }
  };

  // ─── Telemetry Calculations ──────────────────────────────────────────────────
  const totalAudits = reports.length;
  const compromisedCount = reports.filter(r => getStatusType(r.status, r.verdict) === "critical").length;
  const compromiseRate = totalAudits > 0 ? Math.round((compromisedCount / totalAudits) * 100) : 0;
  
  const targetCounts = reports.reduce((acc, r) => {
    const t = r.target_url || "Unknown";
    acc[t] = (acc[t] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const topTarget = Object.keys(targetCounts).sort((a, b) => targetCounts[b] - targetCounts[a])[0] || "None";
  
  const lastBreachReport = reports.find(r => getStatusType(r.status, r.verdict) === "critical");
  
  // Format relative time helper
  const getRelativeTime = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.round(diffMs / 60000);
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  const filteredReports = reports.filter(r => 
    (r.target_url || "").toLowerCase().includes(searchQuery.toLowerCase()) || 
    r.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#0a0a0a]">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-600" />
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col bg-transparent overflow-hidden p-6 gap-5 font-['Elms_Sans'] relative">
      
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

      {/* ─── Modals ─── */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-md rounded-2xl border border-red-500/20 bg-zinc-950 p-8 shadow-2xl">
            <div className="mb-6 flex flex-col items-center gap-4 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full border border-red-500/30 bg-red-500/10">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold tracking-tight text-white">Purge All Reports?</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-500">
                  This will permanently delete <span className="font-mono text-zinc-300">{reports.length}</span> report{reports.length !== 1 ? "s" : ""} from the database. This action{" "}
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
                {clearing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                {clearing ? "Purging..." : "Confirm Purge"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Top Telemetry Scorecards (12%) ─── */}
      <div className="shrink-0 flex gap-4 h-20 relative z-10">
        {/* Total Audits */}
        <div className="flex-1 rounded-xl flex flex-col justify-center px-6 relative overflow-hidden group"
             style={{ background: "rgba(16,16,18,0.2)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}>
          <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold mb-0.5">Total Audits</span>
          <span className="text-2xl font-bold text-white tabular-nums tracking-tight">{totalAudits}</span>
        </div>

        {/* Compromise Rate */}
        <div className="flex-1 rounded-xl flex flex-col justify-center px-6 relative overflow-hidden group"
             style={{ background: "rgba(16,16,18,0.2)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}>
          <div className="absolute -inset-10 bg-gradient-to-r from-red-600/20 via-purple-600/20 to-transparent blur-2xl opacity-30" />
          <div className="relative z-10 flex items-end justify-between">
            <div className="flex flex-col">
              <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold mb-0.5">Compromise Rate</span>
              <span className="text-2xl font-bold tabular-nums tracking-tight" 
                    style={{ WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundImage: "linear-gradient(to right, #ef4444, #f59e0b)" }}>
                {compromiseRate}%
              </span>
            </div>
            {/* Sparkline mock */}
            <div className="flex items-end gap-1 mb-1 opacity-80">
              <div className="w-1.5 h-1.5 bg-red-500/40 rounded-full" />
              <div className="w-1.5 h-2.5 bg-red-500/60 rounded-full" />
              <div className="w-1.5 h-3.5 bg-red-500/80 rounded-full" />
              <div className="w-1.5 h-5 bg-red-500 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
            </div>
          </div>
        </div>

        {/* Top Target */}
        <div className="flex-[1.5] rounded-xl flex flex-col justify-center px-6 relative overflow-hidden group"
             style={{ background: "rgba(16,16,18,0.2)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}>
          <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold mb-0.5">Most Audited Target</span>
          <span className="text-lg font-bold text-zinc-200 truncate pr-4">{topTarget}</span>
        </div>

        {/* Last Breach */}
        <div className="flex-1 rounded-xl flex flex-col justify-center px-6 relative overflow-hidden group"
             style={{ background: "rgba(16,16,18,0.2)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}>
          <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold mb-0.5">Last Breach</span>
          <span className="text-lg font-bold text-red-400">{lastBreachReport ? getRelativeTime(lastBreachReport.created_at) : "Never"}</span>
        </div>
      </div>

      {/* ─── Bottom Split (88%) ─── */}
      <div className="flex-1 flex gap-4 min-h-0 relative z-10">
        
        {/* LEFT COLUMN: 30% List */}
        <div className="w-[30%] shrink-0 flex flex-col gap-4 rounded-xl relative overflow-hidden"
             style={{ background: "rgba(14,14,16,0.40)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}>
          
          {/* Search Bar */}
          <div className="shrink-0 p-4 pb-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input 
                type="text" 
                placeholder="Search URL or ID..." 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-black/40 border border-white/5 rounded-lg py-2.5 pl-9 pr-4 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-white/20 transition-colors"
              />
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto px-4 pb-4 no-scrollbar flex flex-col gap-2.5">
            {filteredReports.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-zinc-600 p-8 text-center">
                <ShieldCheck className="w-8 h-8 mb-3 opacity-50" />
                <span className="text-sm">No reports match your search.</span>
              </div>
            ) : (
              filteredReports.map((r) => {
                const isSelected = selectedReport?.id === r.id;
                const type = getStatusType(r.status, r.verdict);
                
                // Color badges
                let badgeClass = "bg-zinc-800 text-zinc-400";
                let icon = <Activity className="w-3 h-3" />;
                if (type === "critical") { badgeClass = "bg-red-500/10 text-red-400 border-red-500/20"; icon = <Zap className="w-3 h-3" />; }
                else if (type === "info") { badgeClass = "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"; icon = <Fingerprint className="w-3 h-3" />; }
                else if (type === "warning") { badgeClass = "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"; icon = <AlertTriangle className="w-3 h-3" />; }
                else if (type === "action") { badgeClass = "bg-purple-500/10 text-purple-400 border-purple-500/20"; icon = <Terminal className="w-3 h-3" />; }

                return (
                  <div 
                    key={r.id} 
                    onClick={() => setSelectedReport(r)}
                    className={`cursor-pointer rounded-lg p-3 flex flex-col gap-2 border transition-all duration-200 ${
                      isSelected ? "bg-white/5 border-white/10" : "bg-transparent border-transparent hover:bg-white/[0.02] hover:border-white/5"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest">{r.id.split("-")[0]}</span>
                      <span className="text-[10px] text-zinc-500">{getRelativeTime(r.created_at)}</span>
                    </div>
                    <div className="flex items-start justify-between gap-2 min-w-0">
                      <span className="text-sm font-semibold text-zinc-200 truncate leading-snug min-w-0 flex-1">{r.target_url}</span>
                      <div className={`shrink-0 flex items-center justify-center w-5 h-5 rounded-md border ${badgeClass}`}>
                        {icon}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Purge Footer */}
          {reports.length > 0 && (
            <div className="shrink-0 p-4 border-t border-white/5 bg-black/20">
              <button
                onClick={() => setShowConfirm(true)}
                className="w-full flex items-center justify-center gap-2 rounded-lg border border-red-500/20 bg-red-500/5 py-2.5 text-xs font-semibold uppercase tracking-widest text-red-500/70 transition-all hover:bg-red-500/10 hover:text-red-400"
              >
                <Trash2 className="w-3.5 h-3.5" /> Purge
              </button>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: 70% Viewer */}
        <div className="flex-1 flex flex-col rounded-xl overflow-hidden relative"
             style={{ background: "rgba(10,10,12,0.6)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.04)" }}>
          
          {selectedReport ? (
            <>
              {/* Header */}
              <div className="shrink-0 px-6 py-4 border-b border-white/5 flex items-center justify-between bg-black/20 z-10">
                <div className="flex flex-col gap-1 min-w-0">
                  <h3 className="text-lg font-semibold text-white tracking-tight truncate max-w-xl">{selectedReport.target_name || selectedReport.target_url}</h3>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-zinc-500">{new Date(selectedReport.created_at).toLocaleString()}</span>
                    <span className="text-zinc-600 text-xs">•</span>
                    <span className="font-mono text-xs text-zinc-500">{selectedReport.id}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownload(selectedReport.report_file_url, `report-${selectedReport.id}.md`)}
                    disabled={!selectedReport.report_file_url}
                    className="flex items-center gap-2 rounded-lg bg-white text-black px-4 py-2 text-sm font-semibold transition-colors hover:bg-zinc-200 disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <Download className="w-4 h-4" /> Download
                  </button>
                </div>
              </div>

              {/* Markdown Content */}
              <div className="flex-1 overflow-y-auto p-8 no-scrollbar relative">
                {markdownLoading ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-zinc-600" />
                  </div>
                ) : (
                  <div className="prose prose-invert prose-zinc max-w-none 
                    prose-headings:font-semibold prose-headings:tracking-tight prose-headings:mt-8 prose-headings:mb-4
                    prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl
                    prose-p:text-zinc-400 prose-p:leading-loose prose-p:text-[15px] prose-p:mb-6
                    prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:underline
                    prose-strong:text-zinc-200 prose-code:text-rose-300 prose-code:bg-rose-500/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none
                    prose-pre:bg-[#0a0a0c] prose-pre:border prose-pre:border-white/5 prose-pre:p-6 prose-pre:rounded-xl prose-pre:my-6
                    prose-hr:border-white/5 prose-hr:my-8
                    prose-table:w-full prose-table:border-collapse prose-table:border-hidden prose-table:my-8
                    prose-th:bg-white/5 prose-th:p-4 prose-th:text-left prose-th:text-zinc-200 prose-th:border prose-th:border-white/10
                    prose-td:p-4 prose-td:border prose-td:border-white/5 prose-td:text-zinc-400
                    prose-tr:border-b prose-tr:border-white/5 hover:prose-tr:bg-white/[0.02] transition-colors
                    prose-ul:my-6 prose-li:my-2 prose-li:text-zinc-400">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Block javascript: hrefs and force safe link attributes
                        a: ({ href, children }) => {
                          const safeHref = href && !href.toLowerCase().startsWith("javascript:") ? href : "#";
                          return (
                            <a href={safeHref} target="_blank" rel="noopener noreferrer">
                              {children}
                            </a>
                          );
                        },
                        // Custom table components for premium styling and horizontal scroll wrapper
                        table: ({ children }) => (
                          <div className="w-full overflow-x-auto border border-white/5 rounded-xl my-6 bg-black/20">
                            <table className="w-full border-collapse text-left text-sm text-zinc-400">
                              {children}
                            </table>
                          </div>
                        ),
                        th: ({ children }) => (
                          <th className="bg-white/5 p-4 text-left text-[11px] font-semibold uppercase tracking-wider text-zinc-300 border-b border-white/10">
                            {children}
                          </th>
                        ),
                        td: ({ children }) => (
                          <td className="p-4 text-zinc-400 border-b border-white/5 font-mono text-[13px]">
                            {children}
                          </td>
                        ),
                        tr: ({ children }) => (
                          <tr className="hover:bg-white/[0.01] transition-colors border-b border-white/5 last:border-0">
                            {children}
                          </tr>
                        ),
                        // Monospace dark blockquote for terminal logs/payloads
                        blockquote: ({ children }) => (
                          <blockquote className="my-4 border-l-2 border-red-500/50 bg-[#070709] p-4 rounded-r-lg font-mono text-[12.5px] text-zinc-400 leading-relaxed shadow-sm">
                            {children}
                          </blockquote>
                        ),
                        // Intercept FINDING headers to style them as alert blocks
                        h3: ({ children }) => {
                          const text = String(children || "");
                          if (text.includes("FINDING-")) {
                            return (
                              <div className="mt-8 mb-4 border border-red-500/20 bg-red-500/5 rounded-xl p-4 shadow-lg shadow-red-950/10">
                                <h3 className="text-base font-semibold text-red-400 flex items-center gap-2 m-0">
                                  {children}
                                </h3>
                              </div>
                            );
                          }
                          return <h3 className="text-lg font-semibold text-white tracking-tight mt-8 mb-4">{children}</h3>;
                        }
                      }}
                    >
                      {markdownContent}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-600">
              <FileText className="w-12 h-12 mb-4 opacity-30" />
              <p className="text-sm">Select a report to view its contents.</p>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
}
