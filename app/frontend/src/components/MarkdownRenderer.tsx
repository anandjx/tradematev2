"use client";

import React from "react";

/**
 * Shared Markdown Renderer — centralized, zero-dependency.
 * Handles: headings, bullets, numbered lists, bold, italic, tables, HRs.
 */
export function MarkdownRenderer({ content, className }: { content: string; className?: string }) {
    const lines = content.split("\n");
    const elements: React.ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];

        // Horizontal rule
        if (/^---+$/.test(line.trim())) {
            elements.push(<hr key={i} className="my-4 border-slate-200/60" />);
            i++;
            continue;
        }

        // Table detection: line contains pipes and next line is separator
        if (line.includes("|") && i + 1 < lines.length && /^\|?[\s-:|]+\|/.test(lines[i + 1])) {
            const tableLines: string[] = [line];
            let j = i + 1;
            while (j < lines.length && lines[j].includes("|")) {
                tableLines.push(lines[j]);
                j++;
            }
            elements.push(<MarkdownTable key={i} lines={tableLines} />);
            i = j;
            continue;
        }

        // Headers
        const headerMatch = line.match(/^(#{1,6})\s+(.+)/);
        if (headerMatch) {
            const level = headerMatch[1].length;
            const text = headerMatch[2];
            if (level <= 2) {
                elements.push(
                    <h5 key={i} className="text-lg font-bold text-indigo-900 mt-5 mb-2 border-b border-slate-200/60 pb-1">
                        <InlineMarkdown text={text} />
                    </h5>
                );
            } else if (level === 3) {
                elements.push(
                    <h6 key={i} className="text-base font-bold text-slate-800 mt-4 mb-1.5">
                        <InlineMarkdown text={text} />
                    </h6>
                );
            } else {
                elements.push(
                    <h6 key={i} className="text-sm font-semibold text-slate-700 mt-3 mb-1">
                        <InlineMarkdown text={text} />
                    </h6>
                );
            }
            i++;
            continue;
        }

        // Bullet points (top-level and nested)
        const bulletMatch = line.match(/^(\s*)[*\-]\s+(.*)/);
        if (bulletMatch) {
            const indent = bulletMatch[1].length;
            const text = bulletMatch[2];
            const ml = indent >= 4 ? "ml-6" : indent >= 2 ? "ml-4" : "ml-2";
            elements.push(
                <div key={i} className={`flex gap-2 ${ml} mb-0.5`}>
                    <span className="text-blue-500/70 mt-1 shrink-0">•</span>
                    <span className="text-slate-700 text-sm leading-relaxed">
                        <InlineMarkdown text={text} />
                    </span>
                </div>
            );
            i++;
            continue;
        }

        // Numbered lists
        const numberedMatch = line.match(/^(\s*)\d+\.\s+(.*)/);
        if (numberedMatch) {
            const indent = numberedMatch[1].length;
            const text = numberedMatch[2];
            const ml = indent >= 2 ? "ml-4" : "ml-2";
            elements.push(
                <div key={i} className={`flex gap-2 ${ml} mb-0.5`}>
                    <span className="text-slate-400 mt-0.5 text-xs shrink-0 font-mono">{line.match(/^\s*(\d+)\./)?.[1]}.</span>
                    <span className="text-slate-700 text-sm leading-relaxed">
                        <InlineMarkdown text={text} />
                    </span>
                </div>
            );
            i++;
            continue;
        }

        // Empty lines
        if (line.trim() === "") {
            elements.push(<div key={i} className="h-1.5" />);
            i++;
            continue;
        }

        // Normal paragraph
        elements.push(
            <p key={i} className="text-slate-700 text-sm leading-relaxed">
                <InlineMarkdown text={line} />
            </p>
        );
        i++;
    }

    return <div className={className || "space-y-0.5"}>{elements}</div>;
}

/**
 * Inline markdown: **bold**, *italic*, and combinations.
 */
function InlineMarkdown({ text }: { text: string }) {
    // Split on **bold** and *italic* patterns
    const parts = text.split(/(\*\*.*?\*\*|\*[^*]+?\*)/g);

    return (
        <>
            {parts.map((part, j) => {
                if (part.startsWith("**") && part.endsWith("**")) {
                    return (
                        <strong key={j} className="text-slate-900 font-semibold">
                            {part.slice(2, -2)}
                        </strong>
                    );
                }
                if (part.startsWith("*") && part.endsWith("*") && !part.startsWith("**")) {
                    return (
                        <em key={j} className="text-slate-600">
                            {part.slice(1, -1)}
                        </em>
                    );
                }
                return <React.Fragment key={j}>{part}</React.Fragment>;
            })}
        </>
    );
}

/**
 * Simple pipe-delimited table renderer.
 */
function MarkdownTable({ lines }: { lines: string[] }) {
    const parseRow = (line: string) =>
        line.split("|").map((c) => c.trim()).filter(Boolean);

    const headers = parseRow(lines[0]);
    // Skip separator line (index 1)
    const rows = lines.slice(2).map(parseRow);

    return (
        <div className="overflow-x-auto my-3">
            <table className="min-w-full text-sm border border-slate-200/60 rounded-lg overflow-hidden">
                <thead>
                    <tr className="bg-slate-50/80">
                        {headers.map((h, i) => (
                            <th key={i} className="px-3 py-1.5 text-left text-xs font-semibold text-slate-600 border-b border-slate-200/60">
                                <InlineMarkdown text={h} />
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, ri) => (
                        <tr key={ri} className={ri % 2 === 0 ? "bg-white/40" : "bg-slate-50/40"}>
                            {row.map((cell, ci) => (
                                <td key={ci} className="px-3 py-1.5 text-slate-700 border-b border-slate-100/60">
                                    <InlineMarkdown text={cell} />
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
