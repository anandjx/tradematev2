"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCoAgent, useCoAgentStateRender } from "@copilotkit/react-core";

// New captivating components
import { MarketAnalysisCard } from "@/components/MarketAnalysisCard";
import { TechnicalAnalysisCard } from "@/components/TechnicalAnalysisCard";
import { OracleForecastCard } from "@/components/OracleForecastCard";
import { QuantSynthesisCard } from "@/components/QuantSynthesisCard";
import { StrategicBlueprintCard } from "@/components/StrategicBlueprintCard";
import { PriceTimeseriesCard } from "@/components/PriceTimeseriesCard";

import type { AgentState } from "@/lib/types";

/* ======================================================
   Reusable Agent Configuration
====================================================== */
const AGENT_CONFIG = {
  agentName: "trademate",
  productName: "TradeMate",
  tagline: "Market intelligence, disciplined",
  company: "AJx",
  totalStages: 7,
};

/* ======================================================
   Pipeline Stage Mapping
====================================================== */
const STAGE_ORDER = [
  "market_scan",
  "technical_analysis",
  "oracle_forecast",
  "quant_synthesis",
  "strategy_formulation",
  "report_generation",
  "presentation"
];

const STAGE_CONFIG: Record<string, { label: string; icon: string; description: string }> = {
  market_scan: { label: "Market Analysis", icon: "📊", description: "High-signal analysis of market sentiment and fundamental drivers." },
  technical_analysis: { label: "Technical Analysis", icon: "📈", description: "Quantitative assessment of price structure, momentum, and volatility." },
  oracle_forecast: { label: "Oracle Forecast", icon: "🔮", description: "Predictions using a SOTA Transformer model trained on 400 Billion real world data points." },
  quant_synthesis: { label: "Quantitative Synthesis", icon: "🧮", description: "Evidence-weighted integration of narratives, technicals and forecasts." },
  strategy_formulation: { label: "Strategy Blueprint", icon: "♟️", description: "Conditional strategy frameworks derived from the synthesis." },
  report_generation: { label: "Generating Report", icon: "📄", description: "Compiling institutional-grade equity research HTML." },
  presentation: { label: "Report Ready", icon: "📋", description: "Structured, publication-ready investment report." },
};

export default function Home() {
  const { state } = useCoAgent<AgentState>({
    name: AGENT_CONFIG.agentName,
  });

  useCoAgentStateRender<AgentState>({
    name: AGENT_CONFIG.agentName,
    render: ({ state }) => {
      if (!state || !state.pipeline_stage) return null;
      const stageInfo = STAGE_CONFIG[state.pipeline_stage] || { label: state.pipeline_stage, icon: "⚙️" };
      return (
        <div className="glass px-4 py-2">
          <span className="text-sm text-slate-600">
            Agent processing: <span className="text-slate-900 font-medium">{stageInfo.icon} {stageInfo.label}</span>
          </span>
        </div>
      );
    },
  });

  // Determine current stage index
  const currentStageIndex = state?.pipeline_stage
    ? STAGE_ORDER.indexOf(state.pipeline_stage)
    : -1;

  // Check which components should be visible
  const showMarket = currentStageIndex >= 0 || state?.market_analysis || state?.market_analyst_report;
  const showTechnical = currentStageIndex >= 1 || state?.technical_analysis;
  const showOracle = currentStageIndex >= 2 || state?.oracle_forecast;
  const showQuant = currentStageIndex >= 3 || state?.quant_synthesis;
  const showStrategy = currentStageIndex >= 4 || state?.strategic_report;

  return (
    <CopilotSidebar
      defaultOpen={false}
      clickOutsideToClose={true}
      labels={{
        title: AGENT_CONFIG.productName,
        initial: `

👋 Welcome to **TradeMate**

Enter a **stock, crypto, ETF, commodity or futures** to begin.
You can use either the **ticker** or the **asset name**.

**Examples:**    
• AAPL or Apple  
• NVDA or NVIDIA  
• PRG.DE or Procter & Gamble **Germany**  
• TCS or Tata Consultancy Services   
• 7203.T or Toyota Motor **Japan**    
• BTC-USD or Bitcoin  
• SPY (ETF)  
• GOLD or XAUUSD  

I’ll guide you through a structured analysis covering:

**📊 Market Analysis** – sentiment and fundamental context.  
**📈 Technical Indicators** – price structure, momentum, and volatility.  
**🔮 Price Forecasts** – probabilistic path and uncertainty using SOTA Transformer model.  
**♟️ Strategy Blueprint** – conditional frameworks, with an option to **download the full report**.

**⚠️ IMPORTANT**: Once your query is confirmed, you can close this sidebar using the **X** button (top-right) to instantly view the full-screen interactive report updating live.  

It usually takes about **3 to 5 minutes** after confirmation of the ticker, for the analysis to begin and generate the report.
`,
      }}
    >
      <main className="min-h-screen relative z-10">
        <div className="max-w-6xl mx-auto p-10">

          {/* ================= HEADER ================= */}
          <header className="mb-10 glass p-8 rounded-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-teal-900">
                  {AGENT_CONFIG.productName}
                </h1>
                <p className="text-slate-600 text-lg mt-2">
                  {AGENT_CONFIG.tagline}
                  <span className="mx-2 text-slate-300">|</span>
                  A product by <span className="font-medium text-slate-700">{AGENT_CONFIG.company}</span>
                </p>
              </div>

              {/* Live Status Indicator */}
              {state?.pipeline_stage && (
                <div className="flex items-center gap-3 px-4 py-2 glass rounded-full">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-sm font-medium text-slate-700">
                    {STAGE_CONFIG[state.pipeline_stage]?.icon} {STAGE_CONFIG[state.pipeline_stage]?.label || "Processing..."}
                  </span>
                </div>
              )}
            </div>

            {/* Target Ticker Display */}
            {state?.target_ticker && (
              <div className="mt-6 flex items-center gap-4">
                <span className="text-slate-500">Analyzing:</span>
                <span className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-cyan-500 text-white font-bold rounded-xl shadow-lg">
                  {state.target_ticker}
                </span>
              </div>
            )}
          </header>

          {/* ================= PIPELINE PROGRESS ================= */}
          {state?.pipeline_stage && (
            <div className="mb-10 glass p-6 rounded-2xl">
              <h3 className="text-sm font-medium text-slate-600 mb-4">Analysis Pipeline</h3>
              <div className="flex items-center justify-between">
                {STAGE_ORDER.map((stage, idx) => {
                  const stageInfo = STAGE_CONFIG[stage];
                  const isCompleted = state.stages_completed?.includes(stage);
                  const isCurrent = state.pipeline_stage === stage;
                  const isPending = idx > currentStageIndex;

                  return (
                    <div key={stage} className="flex items-center">
                      {/* Stage Indicator */}
                      <div className="flex flex-col items-center">
                        <div className={`
                          w-12 h-12 rounded-full flex items-center justify-center text-xl
                          transition-all duration-500
                          ${isCompleted ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30" : ""}
                          ${isCurrent ? "bg-gradient-to-br from-indigo-500 to-cyan-500 text-white shadow-lg shadow-indigo-500/30 animate-pulse" : ""}
                          ${isPending ? "bg-slate-100 text-slate-400" : ""}
                        `}>
                          {isCompleted ? "✓" : stageInfo.icon}
                        </div>
                        <span className={`text-xs mt-2 text-center max-w-[80px] ${isCurrent ? "text-indigo-600 font-medium" : "text-slate-500"}`}>
                          {stageInfo.label}
                        </span>
                      </div>

                      {/* Connector */}
                      {idx < STAGE_ORDER.length - 1 && (
                        <div className={`h-0.5 w-8 mx-2 transition-all duration-500 ${isCompleted ? "bg-emerald-500" : "bg-slate-200"
                          }`} />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ================= INTERACTIVE COMPONENTS ================= */}
          {state?.target_ticker && (
            <div className="space-y-8">
              {/* Row 0: Price Surface (Isolated — no agent) */}
              <PriceTimeseriesCard ticker={state.target_ticker} />

              {/* Row 1: Market & Technical */}
              <div className="grid md:grid-cols-[2fr_1fr] gap-6">
                {showMarket && (
                  <MarketAnalysisCard
                    data={{
                      ...state.market_analysis,
                      report: state.market_analyst_report || state.market_analysis?.report,
                    }}
                    ticker={state.target_ticker}
                    isLoading={state.pipeline_stage === "market_scan" && !state.market_analysis && !state.market_analyst_report}
                  />
                )}

                {showTechnical && (
                  <TechnicalAnalysisCard
                    data={state.technical_analysis}
                    ticker={state.target_ticker}
                    currentPrice={state.market_analysis?.current_price}
                    marketCap={state.market_analysis?.market_cap}
                    isLoading={state.pipeline_stage === "technical_analysis" && !state.technical_analysis}
                  />
                )}
              </div>

              {/* Row 2: Oracle Forecast */}
              {showOracle && (
                <OracleForecastCard
                  data={state.oracle_forecast}
                  forecastData={state.oracle_forecast?.forecast}
                  currentPrice={state.technical_analysis?.price || state.market_analysis?.current_price}
                  ticker={state.target_ticker}
                  isLoading={state.pipeline_stage === "oracle_forecast" && !state.oracle_forecast}
                />
              )}

              {/* Row 3: Quant Synthesis */}
              {showQuant && (
                <QuantSynthesisCard
                  data={state.quant_synthesis}
                  ticker={state.target_ticker}
                  isLoading={state.pipeline_stage === "quant_synthesis" && !state.quant_synthesis}
                />
              )}

              {/* Row 4: Strategic Blueprint */}
              {showStrategy && (
                <StrategicBlueprintCard
                  data={state.strategic_report}
                  ticker={state.target_ticker}
                  isLoading={state.pipeline_stage === "strategy_formulation" && !state.strategic_report}
                  reportHtml={state.equity_report_html}
                />
              )}
            </div>
          )}

          {/* ================= WELCOME STATE ================= */}
          {!state?.target_ticker && (
            <div className="glass p-14 text-center">
              <div className="text-7xl mb-6">📈</div>

              <h2 className="text-3xl font-semibold text-slate-700 mb-4">
                Discover the Optimal Strategy for your Portfolio
              </h2>

              <p className="text-slate-600 max-w-xl mx-auto mb-10 text-lg leading-relaxed">
                Enter your target ticker in the chat to receive
                AI-driven market research, quantitative forecasting and
                strategic blueprints.
                <br />
                <span className="mt-2 inline-block text-slate-500 text-base">
                  To begin, click the <span className="font-medium text-slate-700">💬 chat bubble</span> in the lower-right corner.
                </span>
              </p>

              <div className="grid md:grid-cols-5 gap-4 max-w-4xl mx-auto">
                {STAGE_ORDER.slice(0, 5).map((stage) => {
                  const info = STAGE_CONFIG[stage];
                  return (
                    <FeatureCard
                      key={stage}
                      icon={info.icon}
                      title={info.label}
                      description={info.description}
                    />
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </main>
    </CopilotSidebar>
  );
}

/* ================= FEATURE CARD ================= */
function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="glass p-5 text-center transition-all hover:-translate-y-1 hover:shadow-glow">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="font-medium text-slate-800 mb-1 text-sm">
        {title}
      </h3>
      <p className="text-xs text-slate-500 leading-relaxed">
        {description}
      </p>
    </div>
  );
}
