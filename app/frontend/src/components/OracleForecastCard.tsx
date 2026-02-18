"use client";

import { Sparkles, Target, Clock, TrendingUp, TrendingDown } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { currencySymbolForTicker } from "@/lib/currency";

interface OracleForecastData {
    predicted_price?: number;
    confidence_interval?: [number, number];
    model_confidence?: number;
    forecast_horizon?: string;
    history?: { date: string; price: number }[];
}

interface ForecastPoint {
    date: string;
    median_price: number;
    ribbon_lower: number;
    ribbon_upper: number;
    isForecast?: boolean;
}

interface OracleForecastCardProps {
    data?: OracleForecastData;
    forecastData?: ForecastPoint[];
    currentPrice?: number;
    ticker?: string;
    isLoading?: boolean;
}

export function OracleForecastCard({
    data,
    forecastData,
    currentPrice,
    ticker,
    isLoading
}: OracleForecastCardProps) {
    if (isLoading) {
        return (
            <div className="glass p-6 animate-pulse">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20" />
                    <div className="h-6 w-40 bg-slate-200/50 rounded" />
                </div>
                <div className="h-48 bg-slate-200/50 rounded" />
            </div>
        );
    }

    if (!data) return null;

    const priceChange = data.predicted_price && currentPrice
        ? ((data.predicted_price - currentPrice) / currentPrice) * 100
        : 0;
    const isPositive = priceChange >= 0;
    const sym = currencySymbolForTicker(ticker);

    // Prepare Chart Data: Merge History + Forecast
    // 1. History (if available)
    const historyPoints = data.history?.map(h => ({
        date: new Date(h.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        median_price: h.price,
        ribbon_lower: h.price, // Tight ribbon for history
        ribbon_upper: h.price,
        isForecast: false
    })) || [];

    // 2. Forecast (Sample if missing)
    const forecastPoints = (forecastData || generateSampleForecastData(
        historyPoints.length > 0 ? historyPoints[historyPoints.length - 1].median_price : (currentPrice || 100),
        data.predicted_price || 100
    )).map(d => ({
        ...d,
        isForecast: true
    }));

    // Combine
    const chartData = [...historyPoints, ...forecastPoints];

    return (
        <div className="glass p-5 relative overflow-hidden group hover:shadow-glow transition-all duration-500" style={{ border: '2px solid rgba(245, 158, 11, 0.25)' }}>
            {/* Animated gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 via-transparent to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Glowing orb animation */}
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-gradient-to-br from-amber-400/20 to-orange-400/20 rounded-full blur-3xl animate-pulse-slow" />

            {/* Header */}
            <div className="flex items-center justify-between mb-4 relative">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg relative">
                        <Sparkles className="w-6 h-6 text-white" />
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-amber-400 to-orange-400 animate-pulse opacity-50" />
                    </div>
                    <div>
                        <h3 className="font-bold text-lg text-slate-800">Oracle Forecast</h3>
                        <p className="text-sm text-slate-500">{ticker || "Asset"} • TimesFM 2.5</p>
                    </div>
                </div>

                {/* Model Confidence */}
                <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 rounded-full border border-amber-500/30">
                    <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <span className="text-sm font-medium text-amber-700">
                        {((data.model_confidence || 0.8) * 100).toFixed(0)}% Confidence
                    </span>
                </div>
            </div>

            {/* Price Prediction Hero */}
            <div className="glass p-6 rounded-2xl mb-6 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-orange-500/5" />

                <div className="flex items-center justify-between relative">
                    <div>
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-2">
                            <Target className="w-4 h-4" />
                            <span>Predicted Target</span>
                        </div>
                        <p className="text-4xl font-bold text-slate-800">
                            {sym}{data.predicted_price?.toLocaleString() || "---"}
                        </p>

                        {/* Change indicator */}
                        <div className={`flex items-center gap-1 mt-2 ${isPositive ? "text-emerald-500" : "text-rose-500"}`}>
                            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            <span className="font-semibold">{isPositive ? "+" : ""}{priceChange.toFixed(2)}%</span>
                            <span className="text-slate-400 text-sm ml-1">from current</span>
                        </div>
                    </div>

                    {/* Confidence Interval */}
                    <div className="text-right">
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-2">
                            <Clock className="w-4 h-4" />
                            <span>{data.forecast_horizon || "30 days"}</span>
                        </div>
                        <div className="space-y-1">
                            <p className="text-sm text-emerald-600">
                                Upper: {sym}{data.confidence_interval?.[1]?.toLocaleString() || "---"}
                            </p>
                            <p className="text-sm text-rose-600">
                                Lower: {sym}{data.confidence_interval?.[0]?.toLocaleString() || "---"}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Forecast Chart */}
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                        <defs>
                            <linearGradient id="colorPrediction" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#d97706" stopOpacity={0.35} />
                                <stop offset="95%" stopColor="#d97706" stopOpacity={0.02} />
                            </linearGradient>
                            <linearGradient id="colorHistory" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#64748b" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#64748b" stopOpacity={0} />
                            </linearGradient>
                            {/* Asymmetric risk bands — pronounced contrast */}
                            <linearGradient id="colorDownsideRisk" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#475569" stopOpacity={0.45} />
                                <stop offset="100%" stopColor="#64668d" stopOpacity={0.15} />
                            </linearGradient>
                            <linearGradient id="colorUpsideBand" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#a5b4fc" stopOpacity={0.08} />
                                <stop offset="100%" stopColor="#c7d2fe" stopOpacity={0.03} />
                            </linearGradient>
                        </defs>

                        <XAxis
                            dataKey="date"
                            tick={{ fontSize: 10, fill: "#94a3b8" }}
                            tickLine={false}
                            axisLine={false}
                            interval="preserveStartEnd"
                            minTickGap={30}
                        />
                        <YAxis
                            tick={{ fontSize: 10, fill: "#94a3b8" }}
                            tickLine={false}
                            axisLine={false}
                            domain={['auto', 'auto']}
                            unit={sym}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "rgba(255,255,255,0.95)",
                                border: "1px solid rgba(0,0,0,0.1)",
                                borderRadius: "12px",
                                boxShadow: "0 4px 20px rgba(0,0,0,0.1)"
                            }}
                        />

                        {/* Upside band (lighter — less visual weight) */}
                        <Area
                            type="monotone"
                            dataKey="ribbon_upper"
                            stroke="transparent"
                            fill="url(#colorUpsideBand)"
                        />

                        {/* Downside band (darker — heavier visual weight for risk) */}
                        <Area
                            type="monotone"
                            dataKey="ribbon_lower"
                            stroke="transparent"
                            fill="url(#colorDownsideRisk)"
                        />

                        {/* Main prediction line */}
                        <Area
                            type="monotone"
                            dataKey="median_price"
                            stroke="#d97706"
                            strokeWidth={3.5}
                            fill="url(#colorPrediction)"
                            dot={false}
                        />

                        {/* Current price reference */}
                        {currentPrice && (
                            <ReferenceLine
                                y={currentPrice}
                                stroke="#64748b"
                                strokeDasharray="5 5"
                                label={{ value: "Current", position: "left", fontSize: 10, fill: "#64748b" }}
                            />
                        )}
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

// Helper function to generate sample forecast data
function generateSampleForecastData(currentPrice: number, targetPrice: number): ForecastPoint[] {
    const data: ForecastPoint[] = [];
    const days = 30;
    const priceDiff = targetPrice - currentPrice;

    for (let i = 0; i <= days; i += 3) {
        const progress = i / days;
        const basePrice = currentPrice + (priceDiff * progress);
        const volatility = Math.abs(currentPrice) * 0.05 * progress; // Increasing uncertainty

        const date = new Date();
        date.setDate(date.getDate() + i);

        data.push({
            date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            median_price: Number((basePrice + (Math.random() - 0.5) * volatility).toFixed(2)),
            ribbon_lower: Number((basePrice - volatility * 1.5).toFixed(2)),
            ribbon_upper: Number((basePrice + volatility * 1.5).toFixed(2)),
        });
    }

    return data;
}
