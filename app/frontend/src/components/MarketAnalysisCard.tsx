"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Minus, Globe, FileText, ChevronDown, ChevronRight } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface MarketAnalysisData {
    sentiment?: "Bullish" | "Bearish" | "Neutral";
    key_drivers?: string[];
    sector_performance?: string;
    current_price?: number;
    market_cap?: number;
    report?: string; // Full markdown report
}

interface MarketAnalysisCardProps {
    data?: MarketAnalysisData;
    ticker?: string;
    isLoading?: boolean;
}

/**
 * Extract the "Narrative Positioning & Momentum Intelligence" section from the report.
 * Returns { narrativeSection, remainingReport }.
 */
function extractNarrativeSection(report: string): { narrativeSection: string | null; remainingReport: string } {
    // Match heading patterns like "## 5. Narrative Positioning & Momentum Intelligence" or similar
    const headingPattern = /^#{1,4}\s*\d*\.?\s*Narrative\s+Positioning\s*[&\u0026]\s*Momentum\s+Intelligence\s*:?\s*$/im;
    const match = report.match(headingPattern);

    if (!match || match.index === undefined) {
        return { narrativeSection: null, remainingReport: report };
    }

    const startIdx = match.index;
    // Find the next heading of equal or higher level
    const afterSection = report.slice(startIdx + match[0].length);
    const nextHeadingMatch = afterSection.match(/\n#{1,4}\s+\d/);

    let narrativeSection: string;
    let remainingReport: string;

    if (nextHeadingMatch && nextHeadingMatch.index !== undefined) {
        narrativeSection = afterSection.slice(0, nextHeadingMatch.index).trim();
        remainingReport = report.slice(0, startIdx).trim() + "\n" + afterSection.slice(nextHeadingMatch.index).trim();
    } else {
        narrativeSection = afterSection.trim();
        remainingReport = report.slice(0, startIdx).trim();
    }

    return { narrativeSection, remainingReport };
}

/**
 * Extract a one-line market state from the report (e.g. "Expectations Reset", "Risk-On Rally").
 * Looks for patterns like: **Market State:** X, or **Overall Market Regime:** X
 */
function extractMarketState(report: string, sentiment?: string): string | null {
    // Try common patterns the LLM uses
    const patterns = [
        /\*\*Market\s+(?:State|Regime|Condition)\s*:?\*\*\s*:?\s*(.+?)(?:\n|$)/i,
        /Market\s+(?:Underreaction|Overreaction)\s+Watch\s*:?\*\*\s*(.+?)(?:\n|$)/i,
        /\*\*Overall\s+(?:Sentiment|Assessment)\s*:?\*\*\s*:?\s*(.+?)(?:\n|$)/i,
    ];

    for (const pattern of patterns) {
        const match = report.match(pattern);
        if (match) {
            // Clean up the extracted state, remove markdown tokens
            return match[1].replace(/\*\*/g, "").replace(/\*/g, "").trim().slice(0, 80);
        }
    }

    // Fallback: use sentiment if available
    if (sentiment) {
        const sentimentStates: Record<string, string> = {
            Bullish: "Risk-On Posture",
            Bearish: "Defensive Posture",
            Neutral: "Range-Bound Regime",
        };
        return sentimentStates[sentiment] || null;
    }

    return null;
}

export function MarketAnalysisCard({ data, ticker, isLoading }: MarketAnalysisCardProps) {
    const [narrativeExpanded, setNarrativeExpanded] = useState(false);

    if (isLoading) {
        return (
            <div className="glass p-5 animate-pulse">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20" />
                    <div className="h-6 w-40 bg-slate-200/50 rounded" />
                </div>
                <div className="space-y-3">
                    <div className="h-4 bg-slate-200/50 rounded w-3/4" />
                    <div className="h-4 bg-slate-200/50 rounded w-1/2" />
                </div>
            </div>
        );
    }

    if (!data) return null;

    const sentimentConfig = {
        Bullish: { icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/30" },
        Bearish: { icon: TrendingDown, color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/30" },
        Neutral: { icon: Minus, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/30" },
    };

    const config = sentimentConfig[data.sentiment || "Neutral"];
    const SentimentIcon = config.icon;

    // Process report content
    const reportContent = data.report || "";
    const { narrativeSection, remainingReport } = extractNarrativeSection(reportContent);
    const cleanReport = remainingReport.replace(/##\s*War Room Report.*/i, "").trim();
    const marketState = extractMarketState(reportContent, data.sentiment);

    // Extract a one-line summary from the narrative section for collapsed state
    const narrativeSummaryLine = narrativeSection
        ? narrativeSection.split("\n").find((l) => l.trim().length > 10 && !l.startsWith("#"))?.replace(/\*\*/g, "").replace(/\*/g, "").trim().slice(0, 120) || "Momentum signals detected"
        : null;

    return (
        <div className="glass relative overflow-hidden group hover:shadow-glow transition-all duration-500 flex flex-col max-h-[78vh]" style={{ border: "2px solid rgba(59, 130, 246, 0.25)" }}>
            {/* Ambient gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

            {/* ─── STICKY HEADER ─── */}
            <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-md px-5 pt-5 pb-3 border-b border-slate-100/60">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg">
                            <Globe className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h3 className="font-extrabold text-xl bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-blue-700">Market Analysis</h3>
                            <p className="text-sm text-slate-500">{ticker || "Asset"}</p>
                        </div>
                    </div>

                    {/* Sentiment Badge */}
                    <div className={`px-3 py-1.5 rounded-full ${config.bg} ${config.border} border flex items-center gap-1.5`}>
                        <SentimentIcon className={`w-3.5 h-3.5 ${config.color}`} />
                        <span className={`font-semibold text-sm ${config.color}`}>{data.sentiment || "Neutral"}</span>
                    </div>
                </div>
            </div>

            {/* ─── SCROLLABLE BODY ─── */}
            <div className="overflow-y-auto flex-1 px-5 pb-5 scrollbar-thin scrollbar-thumb-slate-300/50 scrollbar-track-transparent">

                {/* Key Drivers */}
                {data.key_drivers && data.key_drivers.length > 0 && (
                    <div className="space-y-1.5 mt-4 mb-4">
                        <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Key Drivers</p>
                        <div className="flex flex-wrap gap-1.5">
                            {data.key_drivers.map((driver, idx) => (
                                <span
                                    key={idx}
                                    className="px-2.5 py-1 bg-slate-100/80 rounded-full text-xs text-slate-600 border border-slate-200/50"
                                >
                                    {driver}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* ─── NARRATIVE POSITIONING WIDGET ─── */}
                {narrativeSection && (
                    <div className="my-4 rounded-xl border border-indigo-200/50 bg-indigo-50/30 overflow-hidden">
                        <button
                            onClick={() => setNarrativeExpanded(!narrativeExpanded)}
                            className="w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-indigo-50/50 transition-colors"
                        >
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-5 rounded-full bg-gradient-to-b from-indigo-500 to-blue-400" />
                                <span className="text-xs font-bold text-indigo-800 uppercase tracking-wider">Narrative Positioning & Momentum</span>
                            </div>
                            {narrativeExpanded
                                ? <ChevronDown className="w-4 h-4 text-indigo-400" />
                                : <ChevronRight className="w-4 h-4 text-indigo-400" />
                            }
                        </button>

                        {/* Collapsed: one-line summary */}
                        {!narrativeExpanded && narrativeSummaryLine && (
                            <div className="px-4 pb-2.5 -mt-0.5">
                                <p className="text-xs text-slate-500 italic truncate">{narrativeSummaryLine}…</p>
                            </div>
                        )}

                        {/* Expanded: full section */}
                        {narrativeExpanded && (
                            <div className="px-4 pb-3 border-t border-indigo-100/60 pt-2.5">
                                <MarkdownRenderer content={narrativeSection} className="space-y-0.5" />
                            </div>
                        )}
                    </div>
                )}

                {/* ─── WAR ROOM INTELLIGENCE ─── */}
                {cleanReport && (
                    <div className="mt-3 pt-3 border-t border-slate-200/60">
                        <div className="flex items-center gap-2 mb-3">
                            <div className="w-1.5 h-5 bg-blue-500 rounded-full" />
                            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wide flex items-center gap-2">
                                <FileText className="w-4 h-4 text-slate-500" />
                                War Room Intelligence
                            </h4>
                        </div>
                        <div className="bg-slate-50/40 p-4 rounded-xl border border-slate-200/40">
                            <MarkdownRenderer content={cleanReport} />
                        </div>
                    </div>
                )}

                {/* Sector Footer */}
                {data.sector_performance && !data.report && (
                    <div className="mt-3 pt-3 border-t border-slate-200/50">
                        <p className="text-xs text-slate-500">
                            Sector: <span className="font-medium text-slate-700">{data.sector_performance}</span>
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
