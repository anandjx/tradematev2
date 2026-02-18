import { ChevronDown, ChevronRight, CheckCircle2, Circle, Loader2 } from "lucide-react";
import type { TimelineStepConfig } from "@/lib/types";

interface CollapsibleStepProps {
    step: TimelineStepConfig;
    stepNumber: number;
    status: "pending" | "in_progress" | "complete";
    isExpanded: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}

export function CollapsibleStep({
    step,
    stepNumber,
    status,
    isExpanded,
    onToggle,
    children,
}: CollapsibleStepProps) {
    return (
        <div className={`border rounded-xl transition-all duration-300 ${status === "in_progress"
                ? "border-blue-500/50 bg-blue-50/50 shadow-sm"
                : status === "complete"
                    ? "border-green-200 bg-white"
                    : "border-gray-100 bg-gray-50/50 opacity-60"
            }`}>
            <button
                onClick={onToggle}
                className="w-full flex items-center justify-between p-4"
            >
                <div className="flex items-center gap-3">
                    {/* Status Icon */}
                    <div className="flex-shrink-0">
                        {status === "complete" ? (
                            <CheckCircle2 className="w-6 h-6 text-green-500" />
                        ) : status === "in_progress" ? (
                            <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                        ) : (
                            <Circle className="w-6 h-6 text-gray-300" />
                        )}
                    </div>

                    {/* Label */}
                    <div className="text-left">
                        <h3 className={`font-semibold ${status === "in_progress" ? "text-blue-700" : "text-gray-900"
                            }`}>
                            {step.label}
                        </h3>
                        {step.tool && status === "in_progress" && (
                            <span className="text-xs text-blue-600 flex items-center gap-1 mt-0.5">
                                Using {step.tool.name} {step.tool.icon}
                            </span>
                        )}
                    </div>
                </div>

                {/* Toggle Icon */}
                <div className="text-gray-400">
                    {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </div>
            </button>

            {/* Content */}
            <div className={`overflow-hidden transition-all duration-300 ${isExpanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"}`}>
                <div className="p-4 pt-0 border-t border-dashed border-gray-200 m-4 mt-0">
                    {children}
                </div>
            </div>
        </div>
    );
}
