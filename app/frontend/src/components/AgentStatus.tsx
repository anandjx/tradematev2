export function AgentStatus({ stage }: { stage?: string }) {
    if (!stage) return null;

    return (
        <div className="flex items-center gap-3 glass px-4 py-2 w-fit rounded-full border border-white/20">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
            <span className="text-sm text-slate-600 font-medium">
                Agent status: <span className="text-slate-900 font-bold capitalize">{stage.replace("_", " ")}</span>
            </span>
        </div>
    );
}
