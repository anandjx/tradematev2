import type { StrategicReport } from "@/lib/types";
import { TrendingUp, TrendingDown, Minus, ArrowRight, ShieldAlert, Target } from "lucide-react";

interface ReportDisplayProps {
    report: StrategicReport;
}

export function StrategicReportCard({ report }: ReportDisplayProps) {
    const score = report.overall_score;
    const scoreBg =
        score >= 75
            ? "from-emerald-500 to-green-600"
            : score >= 50
                ? "from-amber-500 to-orange-600"
                : "from-rose-500 to-red-600";

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            {/* Header */}
            <div className="p-6 bg-gradient-to-r from-slate-50 to-white border-b border-slate-100 flex justify-between items-start">
                <div>
                    <div className="flex items-center gap-3 mb-1">
                        <div className="p-2 bg-white rounded-lg border border-slate-200 shadow-sm">
                            {report.signal === "BUY" ? <TrendingUp className="text-green-600" /> :
                                report.signal === "SELL" ? <TrendingDown className="text-red-600" /> :
                                    <Minus className="text-amber-600" />}
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900">{report.ticker}</h2>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide ${report.signal === "BUY" ? "bg-green-100 text-green-700" :
                                report.signal === "SELL" ? "bg-red-100 text-red-700" :
                                    "bg-amber-100 text-amber-700"
                            }`}>
                            {report.signal}
                        </span>
                    </div>
                    <p className="text-slate-500 text-sm mt-2 flex items-center gap-2">
                        <Target size={14} />
                        Horizon: <span className="font-medium text-slate-700">{report.time_horizon}</span>
                    </p>
                </div>

                {/* Score */}
                <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${scoreBg} flex flex-col items-center justify-center text-white shadow-lg`}>
                    <span className="text-3xl font-bold">{score}</span>
                    <span className="text-[10px] opacity-80 uppercase tracking-wider">Confidence</span>
                </div>
            </div>

            {/* Strategy Section */}
            <div className="p-6">
                <div className="mb-6">
                    <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <ShieldAlert className="text-indigo-600" size={18} />
                        Strategic Plan
                    </h3>
                    <div className="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100 text-indigo-900/80 leading-relaxed font-medium">
                        "{report.strategic_plan.action}"
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                    <StrategyStat label="Entry Target" value={report.strategic_plan.entry_price} prefix="$" />
                    <StrategyStat label="Stop Loss" value={report.strategic_plan.stop_loss} prefix="$" color="text-red-600" />
                    <StrategyStat label="Take Profit" value={report.strategic_plan.take_profit} prefix="$" color="text-green-600" />
                </div>

                {/* Risk Factors */}
                <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Risk Assessment</h4>
                    <div className="space-y-3">
                        {report.strategic_plan.risk_factors.map((risk, i) => (
                            <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
                                <div className={`mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${risk.impact === "High" ? "bg-red-500" : risk.impact === "Medium" ? "bg-amber-500" : "bg-blue-400"
                                    }`} />
                                <div>
                                    <p className="text-sm font-medium text-slate-800">{risk.factor}</p>
                                    <p className="text-xs text-slate-500 mt-1">{risk.mitigation}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function StrategyStat({ label, value, prefix, color = "text-slate-900" }: any) {
    return (
        <div className="p-3 bg-white border border-slate-100 rounded-lg shadow-sm text-center">
            <div className="text-xs text-slate-500 mb-1">{label}</div>
            <div className={`text-lg font-bold ${color}`}>
                {prefix}{value}
            </div>
        </div>
    )
}
