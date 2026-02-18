export interface AgentState {
    // Pipeline Tracking
    pipeline_stage?: "market_scan" | "technical_analysis" | "oracle_forecast" | "quant_synthesis" | "strategy_formulation" | "report_generation" | "presentation";
    stages_completed?: string[];

    // Inputs
    target_ticker?: string;

    // Live Analysis Data (emitted by tools)
    market_analysis?: MarketAnalysis;
    technical_analysis?: TechnicalAnalysis;
    oracle_forecast?: OracleForecast;
    quant_synthesis?: QuantSynthesis;

    // Agent output captures (via output_key)
    market_analyst_report?: string; // Full text from market analyst agent

    // Outputs
    strategic_report?: StrategicReport;
    equity_report_html?: string;  // Deterministic HTML report from report_generator
    html_report_content?: string;
    infographic_base64?: string;
}

export interface QuantSynthesis {
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

export interface StrategicReport {
    ticker: string;
    location_name?: string; // Legacy/Compat
    overall_score: number; // 0-100
    signal: "BUY" | "SELL" | "HOLD";
    time_horizon: "Short-term" | "Medium-term" | "Long-term";
    narrative?: string; // Full Markdown from Strategic Blueprint Agent

    // Sections
    market_analysis: MarketAnalysis;
    technical_analysis: TechnicalAnalysis;
    oracle_forecast: OracleForecast;
    strategic_plan: StrategicPlan;
}

export interface MarketAnalysis {
    sentiment?: "Bullish" | "Bearish" | "Neutral";
    key_drivers?: string[];
    sector_performance?: string;
    current_price?: number;
    market_cap?: number;
    report?: string; // Full markdown report
}

export interface TechnicalAnalysis {
    trend?: "Uptrend" | "Downtrend" | "Sideways";
    rsi?: number;
    macd?: string;
    support_levels?: number[];
    resistance_levels?: number[];
    rating?: number; // 0-10
    price?: number;
    sma_20?: number;
    sma_50?: number;
    bollinger_upper?: number;
    bollinger_lower?: number;
}

export interface OracleForecast {
    predicted_price: number;
    confidence_interval: [number, number];
    model_confidence: number;
    forecast_horizon: string;
    history?: { date: string; price: number }[]; // Historical context
    forecast?: { date: string; median_price: number; ribbon_lower: number; ribbon_upper: number }[]; // Forecast points
}

export interface StrategicPlan {
    action: string; // e.g., "Accumulate on dips"
    entry_price: number;
    stop_loss: number;
    take_profit: number;
    risk_factors: RiskFactor[];
}

export interface RiskFactor {
    factor: string;
    impact: "High" | "Medium" | "Low";
    mitigation: string;
}

export interface TimelineStepConfig {
    id: string;
    label: string;
    stageKey: string;
    tool?: {
        icon: string;
        name: string;
    };
}

export type CollapsedSteps = Record<string, boolean>;
