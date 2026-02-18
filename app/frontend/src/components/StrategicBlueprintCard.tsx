"use client";

import { Crown, Shield, TrendingUp, TrendingDown, Scroll, ChevronDown, ChevronUp, Download, FileText, Loader2 } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { useState, useCallback } from "react";

/* ─── Types ─── */
interface StrategicPlan {
    action?: string;
    entry_price?: number;
    stop_loss?: number;
    take_profit?: number;
    risk_factors?: RiskFactor[];
}

interface RiskFactor {
    factor: string;
    impact: "High" | "Medium" | "Low";
    mitigation?: string;
}

interface StrategicBlueprintData {
    ticker?: string;
    overall_score?: number;
    signal?: "BUY" | "SELL" | "HOLD";
    time_horizon?: string;
    narrative?: string;
    strategic_plan?: StrategicPlan;
}

interface StrategicBlueprintCardProps {
    data?: StrategicBlueprintData;
    ticker?: string;
    isLoading?: boolean;
    reportHtml?: string;
}

/* ─── Signal Themes ─── */
const SIGNAL_CONFIG = {
    BUY: {
        gradient: "from-emerald-500 to-green-500",
        bg: "bg-emerald-500/8",
        border: "border-emerald-500/25",
        text: "text-emerald-600",
        Icon: TrendingUp,
    },
    SELL: {
        gradient: "from-rose-500 to-red-500",
        bg: "bg-rose-500/8",
        border: "border-rose-500/25",
        text: "text-rose-600",
        Icon: TrendingDown,
    },
    HOLD: {
        gradient: "from-amber-500 to-orange-500",
        bg: "bg-amber-500/8",
        border: "border-amber-500/25",
        text: "text-amber-600",
        Icon: Shield,
    },
} as const;

/* ─── Component ─── */
export function StrategicBlueprintCard({ data, ticker, isLoading, reportHtml }: StrategicBlueprintCardProps) {
    const [expanded, setExpanded] = useState(true);
    const [downloadTriggered, setDownloadTriggered] = useState(false);

    /* ── Download handler ── */
    const handleDownload = useCallback(() => {
        if (!reportHtml) return;
        setDownloadTriggered(true);

        const blob = new Blob([reportHtml], { type: "text/html" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${(ticker || data?.ticker || "equity").toUpperCase()}_Research_Report.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setTimeout(() => setDownloadTriggered(false), 2000);
    }, [reportHtml, ticker, data?.ticker]);

    /* Loading skeleton */
    if (isLoading) {
        return (
            <div className="glass p-6 animate-pulse">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-700/20 to-slate-900/20" />
                    <div className="h-6 w-48 bg-slate-200/50 rounded" />
                </div>
                <div className="space-y-3">
                    <div className="h-4 bg-slate-200/50 rounded w-5/6" />
                    <div className="h-4 bg-slate-200/50 rounded w-4/6" />
                    <div className="h-32 bg-slate-200/50 rounded" />
                    <div className="h-20 bg-slate-200/50 rounded" />
                </div>
            </div>
        );
    }

    if (!data) return null;

    const signal = data.signal || "HOLD";
    const config = SIGNAL_CONFIG[signal];
    const SignalIcon = config.Icon;
    const score = data.overall_score || 75;
    const displayTicker = ticker || data.ticker || "Asset";
    const horizon = data.time_horizon || "Medium-term";

    /* Clean narrative: strip the disclaimer (rendered separately) */
    let narrative = data.narrative || "";
    let disclaimer = "";
    const disclaimerIdx = narrative.indexOf("> *This Strategic Blueprint");
    if (disclaimerIdx !== -1) {
        disclaimer = narrative.slice(disclaimerIdx).trim();
        narrative = narrative.slice(0, disclaimerIdx).trim();
    }

    return (
        <div
            className="glass p-5 relative overflow-hidden group hover:shadow-glow transition-all duration-500"
            style={{ border: "2px solid rgba(51, 65, 85, 0.25)" }}
        >
            {/* ── Ambient layers ── */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/[0.03] via-transparent to-amber-500/[0.03] opacity-60 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            <div className="absolute -top-16 -right-16 w-40 h-40 bg-gradient-to-br from-amber-400/10 to-orange-400/10 rounded-full blur-3xl pointer-events-none" />

            {/* ── Header Row ── */}
            <div className="flex items-center justify-between mb-5 relative">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center shadow-lg relative">
                        <Crown className="w-6 h-6 text-amber-400" />
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-amber-400/20 to-orange-400/20 animate-pulse" />
                    </div>
                    <div>
                        <h3 className="font-bold text-lg text-slate-800">Strategic Blueprint</h3>
                        <p className="text-sm text-slate-500">{displayTicker} • {horizon}</p>
                    </div>
                </div>

                {/* Score + Signal */}
                <div className="flex items-center gap-3">
                    <div className="text-right">
                        <p className="text-[10px] text-slate-400 uppercase tracking-wider">Score</p>
                        <p className="text-2xl font-bold text-slate-800">{score}</p>
                    </div>
                    <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-lg`}>
                        <SignalIcon className="w-6 h-6 text-white" />
                    </div>
                </div>
            </div>

            {/* ── Signal Action Banner ── */}
            <div className={`p-4 rounded-2xl mb-5 ${config.bg} ${config.border} border relative overflow-hidden`}>
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 animate-shimmer pointer-events-none" />
                <div className="flex items-center justify-between relative">
                    <div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">Recommended Posture</p>
                        <p className={`text-2xl font-bold ${config.text}`}>{signal}</p>
                    </div>
                    {data.strategic_plan?.action && data.strategic_plan.action !== "Review analysis" && (
                        <p className="text-sm text-slate-600 max-w-[220px] text-right italic">{data.strategic_plan.action}</p>
                    )}
                </div>
            </div>

            {/* ── Download Research Report ── */}
            <div className="mb-5">
                <button
                    onClick={handleDownload}
                    disabled={!reportHtml}
                    className={`w-full relative overflow-hidden rounded-2xl border transition-all duration-500 ${reportHtml
                            ? "bg-gradient-to-r from-slate-800 to-slate-900 border-slate-700 hover:from-slate-700 hover:to-slate-800 hover:shadow-lg hover:shadow-slate-900/20 cursor-pointer group/dl"
                            : "bg-slate-100 border-slate-200 cursor-not-allowed"
                        }`}
                >
                    {/* Shimmer for ready state */}
                    {reportHtml && (
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.06] to-transparent animate-shimmer pointer-events-none" />
                    )}

                    <div className="relative flex items-center justify-between p-4">
                        <div className="flex items-center gap-3">
                            {reportHtml ? (
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-amber-400" />
                                </div>
                            ) : (
                                <div className="w-10 h-10 rounded-xl bg-slate-200 flex items-center justify-center">
                                    <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
                                </div>
                            )}
                            <div className="text-left">
                                <p className={`text-sm font-bold ${reportHtml ? "text-white" : "text-slate-400"}`}>
                                    {reportHtml ? "Equity Research Report" : "Generating Report..."}
                                </p>
                                <p className={`text-xs ${reportHtml ? "text-slate-400" : "text-slate-300"}`}>
                                    {reportHtml
                                        ? "Institutional-grade • 7-section analysis • PDF-ready HTML"
                                        : "Assembling data from all upstream agents"
                                    }
                                </p>
                            </div>
                        </div>

                        {reportHtml && (
                            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-300 ${downloadTriggered
                                    ? "bg-emerald-500/20 text-emerald-400"
                                    : "bg-white/10 text-slate-300 group-hover/dl:bg-amber-500/20 group-hover/dl:text-amber-400"
                                }`}>
                                <Download className={`w-4 h-4 transition-transform duration-300 ${downloadTriggered ? "scale-110" : "group-hover/dl:translate-y-0.5"}`} />
                                <span className="text-xs font-semibold uppercase tracking-wider">
                                    {downloadTriggered ? "Downloaded!" : "Download"}
                                </span>
                            </div>
                        )}
                    </div>
                </button>
            </div>

            {/* ── Full Narrative ── */}
            {narrative && (
                <div className="mb-4">
                    {/* Collapsible header */}
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="w-full flex items-center justify-between mb-3 group/btn"
                    >
                        <div className="flex items-center gap-2">
                            <Scroll className="w-4 h-4 text-amber-600" />
                            <span className="text-sm font-bold text-slate-700 uppercase tracking-wider">
                                Full Strategic Analysis
                            </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-slate-400 group-hover/btn:text-slate-600 transition-colors">
                            <span>{expanded ? "Collapse" : "Expand"}</span>
                            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </div>
                    </button>

                    {/* Narrative Body */}
                    <div
                        className={`transition-all duration-500 ease-in-out overflow-hidden ${expanded ? "max-h-[5000px] opacity-100" : "max-h-0 opacity-0"}`}
                    >
                        <div className="p-4 bg-white/60 rounded-xl border border-slate-200/60 shadow-sm relative overflow-hidden">
                            {/* Left accent bar */}
                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-500 via-slate-400 to-slate-300" />

                            <div className="prose prose-slate max-w-none pl-3">
                                <MarkdownRenderer content={narrative} />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Disclaimer ── */}
            {disclaimer && (
                <div className="mt-3 px-3 py-2 bg-slate-50/60 rounded-lg border border-slate-100/60">
                    <p className="text-[10px] text-slate-400 leading-relaxed italic">
                        {disclaimer.replace(/^>\s*\*?/g, "").replace(/\*$/g, "").trim()}
                    </p>
                </div>
            )}

            {/* ── Fallback: No narrative yet ── */}
            {!narrative && (
                <div className="p-6 text-center text-slate-400 text-sm">
                    <Scroll className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    <p>Strategic analysis will appear here once generated.</p>
                </div>
            )}
        </div>
    );
}
