import type { AgentState } from "@/lib/types";

interface StepOutputContentProps {
    stepId: string;
    state: AgentState;
}

export function StepOutputContent({ stepId, state }: StepOutputContentProps) {
    // This component renders specific details based on the step
    // Since we don't have the granular stream data yet, we render generic placeholders
    // or specific data if available in the state object.

    if (stepId === "market_scan") {
        return (
            <div className="text-sm text-slate-600">
                <p>Scanning global indices and sector performance.</p>
                {state.target_ticker && <p className="mt-2 text-blue-600">Target: <strong>{state.target_ticker}</strong> identified.</p>}
            </div>
        );
    }

    if (stepId === "oracle_forecast") {
        return (
            <div className="text-sm text-slate-600">
                <p>Accessing Google TimesFM 2.5 foundation model on Vertex AI.</p>
                <p className="mt-1">Calculating confidence intervals...</p>
            </div>
        );
    }

    if (stepId === "strategy_synthesis") {
        return (
            <div className="text-sm text-slate-600">
                <p>Synthesizing signals into execution blueprint.</p>
            </div>
        );
    }

    return <div className="text-sm text-slate-400 italic">Processing data...</div>;
}
