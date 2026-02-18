"use client";

import { useState } from "react";
import { FileText, Image as ImageIcon, Download } from "lucide-react";

interface ArtifactViewerProps {
    htmlReport?: string;
    infographic?: string;
}

export function ArtifactViewer({ htmlReport, infographic }: ArtifactViewerProps) {
    const [activeTab, setActiveTab] = useState<"report" | "infographic">("report");

    if (!htmlReport && !infographic) return null;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mt-8">
            {/* Tab header */}
            <div className="flex border-b border-slate-200 bg-slate-50/50">
                {htmlReport && (
                    <button
                        onClick={() => setActiveTab("report")}
                        className={`flex-1 px-4 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${activeTab === "report"
                                ? "bg-white text-blue-700 border-b-2 border-blue-500"
                                : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                            }`}
                    >
                        <FileText size={16} />
                        Executive Report
                    </button>
                )}
                {infographic && (
                    <button
                        onClick={() => setActiveTab("infographic")}
                        className={`flex-1 px-4 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${activeTab === "infographic"
                                ? "bg-white text-blue-700 border-b-2 border-blue-500"
                                : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                            }`}
                    >
                        <ImageIcon size={16} />
                        Infographic
                    </button>
                )}
            </div>

            {/* Tab content */}
            <div className="p-4 bg-slate-50/30">
                {activeTab === "report" && htmlReport && (
                    <div className="space-y-4">
                        <div className="flex justify-end">
                            <button
                                onClick={() => {
                                    const blob = new Blob([htmlReport], { type: "text/html" });
                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement("a");
                                    a.href = url;
                                    a.download = "trademate_executive_report.html";
                                    a.click();
                                    URL.revokeObjectURL(url);
                                }}
                                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                            >
                                <Download size={14} />
                                Download HTML
                            </button>
                        </div>
                        <iframe
                            srcDoc={htmlReport}
                            className="w-full h-[600px] border border-slate-200 rounded-lg bg-white shadow-inner"
                            title="Executive Report"
                            sandbox="allow-same-origin"
                        />
                    </div>
                )}

                {activeTab === "infographic" && infographic && (
                    <div className="space-y-4">
                        <div className="flex justify-end">
                            <a
                                href={infographic}
                                download="trademate_infographic.png"
                                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                            >
                                <Download size={14} />
                                Download Image
                            </a>
                        </div>
                        <img
                            src={infographic}
                            alt="Strategy Infographic"
                            className="w-full rounded-lg shadow-sm border border-slate-200"
                        />
                    </div>
                )}
            </div>
        </div>
    );
}
