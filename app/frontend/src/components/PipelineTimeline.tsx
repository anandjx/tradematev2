"use client";

import { useState, useCallback } from "react";
import type { AgentState, TimelineStepConfig, CollapsedSteps } from "@/lib/types";
import { CollapsibleStep } from "./CollapsibleStep";
import { StepOutputContent } from "./StepOutputContent";

/**
 * Timeline step configurations matching TradeMate pipeline.
 */
const TIMELINE_STEPS: TimelineStepConfig[] = [
    {
        id: "market_scan",
        label: "Market Intelligence",
        stageKey: "market_scan",
        tool: { icon: "📊", name: "MarketAnalyst" },
    },
    {
        id: "technical_analysis",
        label: "Technical Confirmation",
        stageKey: "technical_analysis",
        tool: { icon: "📉", name: "TechnicalAnalyst" },
    },
    {
        id: "oracle_forecast",
        label: "Oracle Prediction",
        stageKey: "oracle_forecast",
        tool: { icon: "🔮", name: "TimesFM 2.5" },
    },
    {
        id: "quant_synthesis",
        label: "Quantitative Synthesis",
        stageKey: "quant_synthesis",
        tool: { icon: "⚖️", name: "QuantSynth" },
    },
    {
        id: "strategy_formulation",
        label: "Strategic Blueprint",
        stageKey: "strategy_formulation",
        tool: { icon: "\uD83E\uDDE0", name: "Strategist" },
    },
    {
        id: "presentation",
        label: "Final Report",
        stageKey: "presentation",
        tool: { icon: "\uD83D\uDCC4", name: "Presenter" },
    },
];

interface PipelineTimelineProps {
    state: AgentState;
    currentStage?: string;
    completedStages: string[];
}

export function PipelineTimeline({
    state,
    currentStage,
    completedStages,
}: PipelineTimelineProps) {
    const [collapsed, setCollapsed] = useState<CollapsedSteps>({});

    const toggleStep = useCallback((stepId: string) => {
        setCollapsed((prev) => ({
            ...prev,
            [stepId]: !prev[stepId],
        }));
    }, []);

    const getStepStatus = useCallback(
        (step: TimelineStepConfig): "pending" | "in_progress" | "complete" => {
            // Logic: If stage is in completed list, it's complete.
            // If currentStage matches, it's in progress.
            if (completedStages.includes(step.stageKey)) return "complete";
            if (currentStage === step.stageKey) return "in_progress";
            return "pending";
        },
        [completedStages, currentStage]
    );

    const completedCount = completedStages.length;
    const progressPercent = Math.round((completedCount / TIMELINE_STEPS.length) * 100);

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
            {/* Header Card */}
            <div className="p-6 bg-gradient-to-r from-slate-50 to-white border-b border-slate-100">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="h-14 w-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg text-white text-2xl">
                            🚀
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-slate-900">
                                {state.target_ticker || "Market Analysis"}
                            </h2>
                            <p className="text-sm text-slate-500">
                                {state.target_ticker ? `Active Session: ${state.target_ticker}` : "Ready to analyze"}
                            </p>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide font-semibold">
                            Pipeline Status
                        </div>
                        <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-blue-600 transition-all duration-500"
                                style={{ width: `${progressPercent}%` }}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Timeline Steps */}
            <div className="p-4 space-y-3">
                {TIMELINE_STEPS.map((step, index) => {
                    const status = getStepStatus(step);

                    // Simple visibility logic: Show all steps to demonstrate the pipeline, 
                    // or hide pending ones if preferred. For "Cool" factor, let's show all but greyed out.
                    return (
                        <CollapsibleStep
                            key={step.id}
                            step={step}
                            stepNumber={index + 1}
                            status={status}
                            isExpanded={!collapsed[step.id]}
                            onToggle={() => toggleStep(step.id)}
                        >
                            <StepOutputContent stepId={step.id} state={state} />
                        </CollapsibleStep>
                    );
                })}
            </div>
        </div>
    );
}
