"use client";

import { TrendingUp, TrendingDown, Activity, Gauge, BarChart2 } from "lucide-react";
import { currencySymbolForTicker } from "@/lib/currency";

interface TechnicalAnalysisData {
    trend?: "Uptrend" | "Downtrend" | "Sideways";
    rsi?: number;
    macd?: string;
    support_levels?: number[];
    resistance_levels?: number[];
    rating?: number;
    price?: number;
    sma_20?: number;
    sma_50?: number;
    bollinger_upper?: number;
    bollinger_lower?: number;
}

interface TechnicalAnalysisCardProps {
    data?: TechnicalAnalysisData;
    ticker?: string;
    currentPrice?: number;
    marketCap?: number;
    isLoading?: boolean;
}

export function TechnicalAnalysisCard({ data, ticker, currentPrice, marketCap, isLoading }: TechnicalAnalysisCardProps) {
    const formatMarketCap = (cap?: number) => {
        if (!cap) return "N/A";
        const s = currencySymbolForTicker(ticker);
        if (cap >= 1e12) return `${s}${(cap / 1e12).toFixed(2)}T`;
        if (cap >= 1e9) return `${s}${(cap / 1e9).toFixed(2)}B`;
        if (cap >= 1e6) return `${s}${(cap / 1e6).toFixed(2)}M`;
        return `${s}${cap.toLocaleString()}`;
    };
    const sym = currencySymbolForTicker(ticker);
    if (isLoading) {
        return (
            <div className="glass p-6 animate-pulse">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20" />
                    <div className="h-6 w-40 bg-slate-200/50 rounded" />
                </div>
                <div className="space-y-3">
                    <div className="h-4 bg-slate-200/50 rounded w-3/4" />
                    <div className="h-20 bg-slate-200/50 rounded" />
                </div>
            </div>
        );
    }

    if (!data) return null;

    const trendConfig = {
        Uptrend: { icon: TrendingUp, color: "text-emerald-500", label: "Bullish Trend" },
        Downtrend: { icon: TrendingDown, color: "text-rose-500", label: "Bearish Trend" },
        Sideways: { icon: Activity, color: "text-amber-500", label: "Consolidating" },
    };

    const config = trendConfig[data.trend || "Sideways"];
    const TrendIcon = config.icon;

    // RSI color based on value
    const getRsiColor = (rsi?: number) => {
        if (!rsi) return "text-slate-500";
        if (rsi < 30) return "text-emerald-500"; // Oversold
        if (rsi > 70) return "text-rose-500"; // Overbought
        return "text-amber-500"; // Neutral
    };

    const getRsiStatus = (rsi?: number) => {
        if (!rsi) return "N/A";
        if (rsi < 30) return "Oversold";
        if (rsi > 70) return "Overbought";
        return "Neutral";
    };

    // RSI gauge percentage for visual display
    const rsiPercentage = data.rsi ? Math.min(100, Math.max(0, data.rsi)) : 50;

    return (
        <div className="glass p-5 relative overflow-hidden group hover:shadow-glow transition-all duration-500" style={{ border: '2px solid rgba(139, 92, 246, 0.25)' }}>
            {/* Animated gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Header */}
            <div className="flex items-center justify-between mb-4 relative">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center shadow-lg">
                        <BarChart2 className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h3 className="font-bold text-lg text-slate-800">Technical Analysis</h3>
                        <p className="text-sm text-slate-500">{ticker || "Asset"}</p>
                    </div>
                </div>

                {/* Trend Badge */}
                <div className="flex items-center gap-2">
                    <TrendIcon className={`w-5 h-5 ${config.color}`} />
                    <span className={`font-semibold text-sm ${config.color}`}>{config.label}</span>
                </div>
            </div>

            {/* Current Price — Prominent Display */}
            <div className="glass p-4 rounded-xl mb-4 bg-gradient-to-r from-white/60 to-slate-50/60">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-1.5 text-slate-500 text-xs mb-1">
                            <span>{sym}</span>
                            <span>Current Price</span>
                        </div>
                        <p className="text-3xl font-extrabold text-slate-800 tracking-tight">
                            {sym}{(currentPrice || data?.price)?.toLocaleString() || "---"}
                        </p>
                    </div>
                    {/* SMA Context */}
                    {data.sma_20 && data.price && (
                        <div className="text-right">
                            <p className="text-[10px] text-slate-400 uppercase tracking-wider">vs 20-Day SMA</p>
                            <p className={`text-sm font-bold ${data.price > data.sma_20 ? 'text-emerald-500' : 'text-rose-500'}`}>
                                {data.price > data.sma_20 ? '▲' : '▼'} {Math.abs(((data.price - data.sma_20) / data.sma_20) * 100).toFixed(1)}%
                            </p>
                            <p className="text-[10px] text-slate-400">
                                {data.price > data.sma_20 ? 'Above' : 'Below'} {sym}{data.sma_20.toFixed(2)}
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* RSI Gauge */}
            <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <Gauge className="w-4 h-4 text-slate-500" />
                        <span className="text-sm font-medium text-slate-600">RSI Index</span>
                    </div>
                    <span className={`font-bold text-lg ${getRsiColor(data.rsi)}`}>
                        {data.rsi?.toFixed(1) || "---"}
                    </span>
                </div>

                {/* RSI Bar */}
                <div className="relative h-3 bg-gradient-to-r from-emerald-500/20 via-amber-500/20 to-rose-500/20 rounded-full overflow-hidden">
                    {/* Marker zones */}
                    <div className="absolute left-[30%] h-full w-px bg-slate-300" />
                    <div className="absolute left-[70%] h-full w-px bg-slate-300" />

                    {/* Current RSI indicator */}
                    <div
                        className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white border-2 border-slate-700 shadow-lg transition-all duration-500"
                        style={{ left: `calc(${rsiPercentage}% - 8px)` }}
                    />
                </div>
                <div className="flex justify-between mt-1 text-xs text-slate-400">
                    <span>Oversold</span>
                    <span>Neutral</span>
                    <span>Overbought</span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="glass p-3 rounded-xl">
                    <p className="text-xs text-slate-500 mb-0.5">MACD Signal</p>
                    <p className={`text-base font-bold ${data.macd === "Bullish" ? "text-emerald-500" : "text-rose-500"}`}>
                        {data.macd || "---"}
                    </p>
                </div>

                <div className="glass p-3 rounded-xl">
                    <p className="text-xs text-slate-500 mb-0.5">RSI Status</p>
                    <p className={`text-base font-bold ${getRsiColor(data.rsi)}`}>
                        {getRsiStatus(data.rsi)}
                    </p>
                </div>
            </div>

            {/* Advanced Indicators (SMA / Bollinger) */}
            <div className="mb-4 pt-3 border-t border-slate-200/50">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Key Moving Averages & Bands</h4>
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-slate-50/50 p-2 rounded border border-slate-100">
                        <p className="text-xs text-slate-400">20-Day SMA</p>
                        <p className={`font-mono text-sm font-semibold ${data.sma_20 && data.price && data.price > data.sma_20 ? 'text-emerald-600' : 'text-rose-600'}`}>
                            {sym}{data.sma_20?.toLocaleString() || "-"}
                        </p>
                    </div>
                    <div className="bg-slate-50/50 p-2 rounded border border-slate-100">
                        <p className="text-xs text-slate-400">50-Day SMA</p>
                        <p className={`font-mono text-sm font-semibold ${data.sma_50 && data.price && data.price > data.sma_50 ? 'text-emerald-600' : 'text-rose-600'}`}>
                            {sym}{data.sma_50?.toLocaleString() || "-"}
                        </p>
                    </div>
                </div>

                {/* Bollinger Bands Visualization */}
                {data.bollinger_upper && data.bollinger_lower && data.price && (
                    <div className="bg-slate-50/50 p-3 rounded-lg border border-slate-100">
                        <div className="flex justify-between text-xs text-slate-500 mb-1">
                            <span>Low: {sym}{data.bollinger_lower.toFixed(1)}</span>
                            <span className="font-semibold text-slate-700">Bollinger Bands</span>
                            <span>High: {sym}{data.bollinger_upper.toFixed(1)}</span>
                        </div>
                        <div className="relative h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div className="absolute inset-0 bg-indigo-100 opacity-50" />
                            {/* Position marker */}
                            <div
                                className="absolute top-0 bottom-0 w-1 bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.6)]"
                                style={{
                                    left: `${Math.min(100, Math.max(0, ((data.price - data.bollinger_lower) / (data.bollinger_upper - data.bollinger_lower)) * 100))}%`
                                }}
                            />
                        </div>
                        <p className="text-center text-[10px] text-slate-400 mt-1">Current Price Position relative to Bands</p>

                        {/* Bollinger Interpretation */}
                        {(() => {
                            const pct = (data.price - data.bollinger_lower) / (data.bollinger_upper - data.bollinger_lower);
                            let interpretation = 'Within Bollinger Bands — range-bound.';
                            if (pct <= 0.25) interpretation = 'Trading near the lower band — potential support zone.';
                            else if (pct >= 0.75) interpretation = 'Trading near the upper band — potential resistance zone.';
                            return (
                                <p className="text-xs text-slate-500 mt-1.5 italic">
                                    <span className="font-medium text-slate-600 not-italic">Volatility:</span>{' '}{interpretation}
                                </p>
                            );
                        })()}
                    </div>
                )}
            </div>

            {/* Support & Resistance */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <p className="text-sm font-medium text-emerald-600 mb-2">Support</p>
                    <div className="space-y-1">
                        {data.support_levels?.map((level, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                <span className="text-xs text-slate-700 font-mono">{sym}{level.toLocaleString()}</span>
                            </div>
                        )) || <span className="text-xs text-slate-400">---</span>}
                    </div>
                </div>

                <div>
                    <p className="text-sm font-medium text-rose-600 mb-2">Resistance</p>
                    <div className="space-y-1">
                        {data.resistance_levels?.map((level, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                                <span className="text-xs text-slate-700 font-mono">{sym}{level.toLocaleString()}</span>
                            </div>
                        )) || <span className="text-xs text-slate-400">---</span>}
                    </div>
                </div>
            </div>
        </div>
    );
}
