"use client";

import { Brain, Zap, CheckCircle, AlertTriangle, BarChart, Newspaper } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

interface QuantSynthesisData {
    ticker?: string;
    synthesis_complete?: boolean;
    summary?: string;
    overall_signal?: "BUY" | "SELL" | "HOLD";
    confidence_score?: number;
    factors?: {
        market: number;
        technical: number;
        forecast: number;
    };
}

interface QuantSynthesisCardProps {
    data?: QuantSynthesisData;
    ticker?: string;
    isLoading?: boolean;
}

export function QuantSynthesisCard({ data, ticker, isLoading }: QuantSynthesisCardProps) {
    if (isLoading) {
        return (
            <div className="glass p-6 animate-pulse">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-blue-500/20" />
                    <div className="h-6 w-40 bg-slate-200/50 rounded" />
                </div>
                <div className="space-y-3">
                    <div className="h-4 bg-slate-200/50 rounded w-3/4" />
                    <div className="h-32 bg-slate-200/50 rounded" />
                </div>
            </div>
        );
    }

    if (!data) return null;

    // Default values for visualization
    const confidenceScore = data.confidence_score || 75;
    const factors = data.factors || { market: 70, technical: 80, forecast: 75 };

    const signalConfig = {
        BUY: { color: "#10b981", bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-600" },
        SELL: { color: "#ef4444", bg: "bg-rose-500/10", border: "border-rose-500/30", text: "text-rose-600" },
        HOLD: { color: "#f59e0b", bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-600" },
    };

    const signal = data.overall_signal || "HOLD";
    const config = signalConfig[signal];

    // Pie chart data
    const pieData = [
        { name: "Score", value: confidenceScore, color: config.color },
        { name: "Remaining", value: 100 - confidenceScore, color: "#e2e8f0" },
    ];

    // Factor bars data
    const factorBars = [
        { label: "Market", value: factors.market, icon: "📊", hint: "News & fundamental health" },
        { label: "Technical", value: factors.technical, icon: "📈", hint: "Chart pattern strength" },
        { label: "Forecast", value: factors.forecast, icon: "🔮", hint: "AI prediction confidence" },
    ];

    return (
        <div className="glass p-5 relative overflow-hidden group hover:shadow-glow transition-all duration-500" style={{ border: '2px solid rgba(99, 102, 241, 0.25)' }}>
            {/* Animated gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Header */}
            <div className="flex items-center justify-between mb-4 relative">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center shadow-lg">
                        <Brain className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h3 className="font-bold text-lg text-slate-800">Quantitative Synthesis</h3>
                        <p className="text-sm text-slate-500">{ticker || data.ticker || "Asset"}</p>
                    </div>
                </div>

                {/* Status Badge */}
                {data.synthesis_complete && (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 rounded-full border border-emerald-500/30">
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                        <span className="text-sm font-medium text-emerald-600">Complete</span>
                    </div>
                )}
            </div>

            {/* Main Content Grid */}
            <div className="grid md:grid-cols-2 gap-4">
                {/* Left: Signal Score */}
                <div className="glass p-4 rounded-2xl relative">
                    <div className="flex flex-col items-center">
                        {/* Pie Chart */}
                        <div className="w-32 h-32 relative">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={35}
                                        outerRadius={50}
                                        startAngle={90}
                                        endAngle={-270}
                                        paddingAngle={0}
                                        dataKey="value"
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>

                            {/* Center text */}
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-2xl font-bold text-slate-800">{confidenceScore}%</span>
                                <span className="text-[9px] text-slate-400 mt-0.5">Signal Alignment</span>
                            </div>
                        </div>

                        {/* Signal Badge */}
                        <div className={`mt-4 px-6 py-2 rounded-full ${config.bg} ${config.border} border`}>
                            <div className="flex items-center gap-2">
                                <Zap className={`w-4 h-4 ${config.text}`} />
                                <span className={`font-bold text-lg ${config.text}`}>{signal}</span>
                            </div>
                        </div>

                        {/* Brief explainer */}
                        <p className="mt-2 text-[10px] text-slate-400 text-center max-w-[180px] leading-tight">
                            {signal === "BUY" && "Signals converge bullish — favorable entry conditions detected."}
                            {signal === "SELL" && "Signals converge bearish — risk of further downside is elevated."}
                            {signal === "HOLD" && "Mixed signals — no clear edge. Wait for stronger confirmation."}
                        </p>
                    </div>
                </div>

                {/* Right: Factor Breakdown */}
                <div className="space-y-4">
                    <p className="text-sm font-medium text-slate-600 flex items-center gap-2">
                        <BarChart className="w-4 h-4" />
                        Factor Weights
                    </p>
                    <p className="text-[10px] text-slate-400 -mt-2 ml-6">How strong is each analysis pillar (0–100)</p>

                    {factorBars.map((factor, idx) => (
                        <div key={idx} className="space-y-1">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-600">{factor.icon} {factor.label}</span>
                                <span className="font-medium text-slate-800">{factor.value}%</span>
                            </div>
                            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-indigo-500 to-blue-500 rounded-full transition-all duration-1000"
                                    style={{ width: `${factor.value}%` }}
                                />
                            </div>
                            <p className="text-[9px] text-slate-400 pl-5">{factor.hint}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Summary Narrative - STRONG TYPOGRAPHY */}
            {data.summary && (
                <div className="mt-4 p-4 bg-white/60 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />

                    <h4 className="flex items-center gap-2 text-sm font-bold text-indigo-900 uppercase tracking-wider mb-3 border-b border-indigo-100 pb-2">
                        <Newspaper className="w-4 h-4" />
                        Executive Synthesis
                    </h4>

                    <div className="prose prose-slate max-w-none">
                        <MarkdownRenderer content={data.summary} />
                    </div>
                </div>
            )}
        </div>
    );
}
