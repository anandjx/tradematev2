import { NextRequest } from "next/server";
import {
    CopilotRuntime,
    ExperimentalEmptyAdapter,
    copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

export const runtime = "nodejs";

// 1. Use Empty Adapter (The backend handles the intelligence)
const serviceAdapter = new ExperimentalEmptyAdapter();

// 2. Define the Runtime and register your Remote Agent
const runtimeInstance = new CopilotRuntime({
    // The 'as any' bypasses the Vercel TypeScript intersection bug
    agents: {
        // "trademate" exactly matches app_name="trademate" in main.py
        trademate: new LangGraphHttpAgent({
            url: process.env.REMOTE_ACTION_URL || "http://localhost:8000",
        }),
    } as any,
});

export const POST = async (req: NextRequest) => {
    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
        runtime: runtimeInstance,
        serviceAdapter,
        endpoint: "/api/copilotkit",
    });

    return handleRequest(req);
};






// import {
//     CopilotRuntime,
//     ExperimentalEmptyAdapter,
//     copilotRuntimeNextJSAppRouterEndpoint,
// } from "@copilotkit/runtime";
// import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";
// import { NextRequest } from "next/server";

// export const runtime = "nodejs";

// // 1. Use Empty Adapter (The backend handles the intelligence)
// const serviceAdapter = new ExperimentalEmptyAdapter();

// // 2. Define the Runtime and register your Remote Agent
// const runtimeInstance = new CopilotRuntime({
//     agents: {
//         trademate: new LangGraphHttpAgent({
//             // "trademate" must match the app_name="trademate" in your main.py
//             url: process.env.REMOTE_ACTION_URL || "http://localhost:8000",
//         }),
//     },
// });

// export const POST = async (req: NextRequest) => {
//     const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
//         runtime: runtimeInstance,
//         serviceAdapter, // Pass the adapter here, NOT the agent
//         endpoint: "/api/copilotkit",
//     });

//     return handleRequest(req);
// };


