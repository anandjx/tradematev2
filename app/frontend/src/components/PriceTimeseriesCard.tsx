"use client";

import { useState, useEffect, useCallback } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown } from "lucide-react";
import { getCurrencySymbol } from "@/lib/currency";

/* ─── Types ─── */
interface SnapshotData {
    ticker: string;
    timeframe: string;
    currency: string;
    price: number;
    change: number;
    change_percent: number;
    market_cap: number | null;
    timestamps: string[];
    prices: number[];
}

interface ChartPoint {
    time: string;
    price: number;
}

interface PriceTimeseriesCardProps {
    ticker: string;
}

/* ─── Constants ─── */
const TIMEFRAMES = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"] as const;
type Timeframe = (typeof TIMEFRAMES)[number];

const TF_LABELS: Record<Timeframe, string> = {
    "1D": "1D",
    "5D": "5D",
    "1M": "1M",
    "6M": "6M",
    YTD: "YTD",
    "1Y": "1Y",
    "5Y": "5Y",
};

/* ─── Component ─── */
export function PriceTimeseriesCard({ ticker }: PriceTimeseriesCardProps) {
    const [activeTimeframe, setActiveTimeframe] = useState<Timeframe>("1M");
    const [data, setData] = useState<SnapshotData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchSnapshot = useCallback(async (tf: Timeframe) => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`/api/price-snapshot?ticker=${encodeURIComponent(ticker)}&timeframe=${tf}`);
            const json = await res.json();
            if (json.error) {
                setError(json.error);
                setData(null);
            } else {
                setData(json);
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : "Network error");
            setData(null);
        } finally {
            setLoading(false);
        }
    }, [ticker]);

    useEffect(() => {
        fetchSnapshot(activeTimeframe);
    }, [activeTimeframe, fetchSnapshot]);

    const handleTabClick = (tf: Timeframe) => {
        setActiveTimeframe(tf);
    };

    /* ─── Derived data ─── */
    const isPositive = (data?.change ?? 0) >= 0;
    const accentColor = isPositive ? "#10b981" : "#ef4444";
    const accentColorLight = isPositive ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.12)";
    const sym = getCurrencySymbol(data?.currency || "USD");

    const chartData: ChartPoint[] = data
        ? data.timestamps.map((t, i) => ({
            time: formatTimestamp(t, activeTimeframe),
            price: data.prices[i],
        }))
        : [];

    // Thin down for performance on intraday
    const thinned = chartData.length > 200
        ? chartData.filter((_, i) => i % Math.ceil(chartData.length / 200) === 0 || i === chartData.length - 1)
        : chartData;

    const priceMin = thinned.length > 0 ? Math.min(...thinned.map((d) => d.price)) : 0;
    const priceMax = thinned.length > 0 ? Math.max(...thinned.map((d) => d.price)) : 0;
    const yPadding = (priceMax - priceMin) * 0.08 || 1;

    return (
        <div
            className="glass p-5 relative overflow-hidden group hover:shadow-glow transition-all duration-500"
            style={{ border: `2px solid ${isPositive ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.2)"}` }}
        >
            {/* Persistent subtle ambient gradient — intensifies on hover */}
            <div
                className="absolute inset-0 opacity-40 group-hover:opacity-70 transition-opacity duration-500 pointer-events-none"
                style={{
                    background: `radial-gradient(ellipse at 30% 20%, ${accentColorLight}, transparent 70%)`,
                }}
            />
            <div
                className="absolute inset-0 pointer-events-none"
                style={{
                    background: isPositive
                        ? "linear-gradient(135deg, rgba(16, 185, 129, 0.04) 0%, rgba(16, 185, 129, 0.01) 50%, transparent 100%)"
                        : "linear-gradient(135deg, rgba(239, 68, 68, 0.04) 0%, rgba(239, 68, 68, 0.01) 50%, transparent 100%)",
                }}
            />

            <div className="relative z-10">
                {/* ─── Header Row ─── */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div
                            className="w-9 h-9 rounded-xl flex items-center justify-center"
                            style={{ background: accentColorLight }}
                        >
                            {isPositive ? (
                                <TrendingUp className="w-4.5 h-4.5" style={{ color: accentColor }} />
                            ) : (
                                <TrendingDown className="w-4.5 h-4.5" style={{ color: accentColor }} />
                            )}
                        </div>
                        <div>
                            <h3 className="font-extrabold text-lg text-slate-800 tracking-tight">
                                {data?.ticker || ticker}
                            </h3>
                            <p className="text-[11px] text-slate-400 uppercase tracking-wider">
                                Price · {data?.currency || "USD"}
                            </p>
                        </div>
                    </div>

                    {/* Price + Change + Market Cap */}
                    {data && (
                        <div className="text-right">
                            <p className="text-2xl font-extrabold text-slate-800 tracking-tight">
                                {sym}
                                {data.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                            <p className={`text-sm font-semibold ${isPositive ? "text-emerald-500" : "text-rose-500"}`}>
                                {isPositive ? "▲" : "▼"} {Math.abs(data.change).toFixed(2)}{" "}
                                ({isPositive ? "+" : ""}{data.change_percent.toFixed(2)}%)
                            </p>
                            {data.market_cap != null && (
                                <p className="text-[11px] text-slate-400 mt-0.5">
                                    MCap {formatMarketCap(data.market_cap, data.currency)}
                                </p>
                            )}
                        </div>
                    )}
                </div>

                {/* ─── Timeframe Tabs ─── */}
                <div className="flex gap-1 mb-4 p-1 rounded-xl bg-slate-100/60">
                    {TIMEFRAMES.map((tf) => (
                        <button
                            key={tf}
                            onClick={() => handleTabClick(tf)}
                            className={`
                                flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all duration-200
                                ${activeTimeframe === tf
                                    ? "bg-white text-slate-800 shadow-sm"
                                    : "text-slate-500 hover:text-slate-700 hover:bg-white/40"
                                }
                            `}
                        >
                            {TF_LABELS[tf]}
                        </button>
                    ))}
                </div>

                {/* ─── Chart Area ─── */}
                <div className="h-[180px] w-full">
                    {loading ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="w-6 h-6 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
                        </div>
                    ) : error ? (
                        <div className="h-full flex items-center justify-center text-sm text-slate-400">
                            {error}
                        </div>
                    ) : thinned.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={thinned} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor={accentColor} stopOpacity={0.25} />
                                        <stop offset="100%" stopColor={accentColor} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis
                                    dataKey="time"
                                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                                    tickLine={false}
                                    axisLine={false}
                                    interval="preserveStartEnd"
                                    minTickGap={40}
                                />
                                <YAxis
                                    domain={[priceMin - yPadding, priceMax + yPadding]}
                                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(v: number) => v.toFixed(0)}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: "rgba(255,255,255,0.85)",
                                        backdropFilter: "blur(8px)",
                                        border: "1px solid rgba(255,255,255,0.6)",
                                        borderRadius: "12px",
                                        fontSize: "12px",
                                        boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
                                    }}
                                    formatter={(value: number | undefined) => [`${sym}${(value ?? 0).toFixed(2)}`, "Price"]}
                                    labelStyle={{ color: "#64748b", fontSize: "11px" }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="price"
                                    stroke={accentColor}
                                    strokeWidth={2}
                                    fill="url(#priceGrad)"
                                    dot={false}
                                    activeDot={{ r: 4, fill: accentColor, stroke: "#fff", strokeWidth: 2 }}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-full flex items-center justify-center text-sm text-slate-400">
                            No data
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

/* ─── Helpers ─── */
function formatTimestamp(iso: string, tf: Timeframe): string {
    const d = new Date(iso);
    if (tf === "1D" || tf === "5D") {
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    if (tf === "1Y" || tf === "5Y") {
        return d.toLocaleDateString([], { month: "short", year: "2-digit" });
    }
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

function formatMarketCap(value: number, currency: string): string {
    const s = getCurrencySymbol(currency);
    if (value >= 1e12) return `${s}${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `${s}${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `${s}${(value / 1e6).toFixed(1)}M`;
    return `${s}${value.toLocaleString()}`;
}
