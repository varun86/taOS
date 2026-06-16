import { useState } from "react";
import { PenLine, LayoutGrid, Plus, Sparkles, Circle } from "lucide-react";
import { DesignView } from "./designstudio/DesignView";
import { TemplatesView } from "./designstudio/TemplatesView";
import { MagicView } from "./designstudio/MagicView";

type DesignStudioView = "design" | "templates" | "elements" | "magic";

const RAIL: { id: DesignStudioView; label: string; icon: typeof PenLine }[] = [
  { id: "design", label: "Design", icon: PenLine },
  { id: "templates", label: "Templates", icon: LayoutGrid },
  { id: "elements", label: "Elements", icon: Plus },
  { id: "magic", label: "Magic", icon: Sparkles },
];

export function DesignStudioApp({ windowId: _windowId }: { windowId: string }) {
  const [view, setView] = useState<DesignStudioView>("design");

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-shell-bg text-shell-text select-none">
      {/* title strip */}
      <div className="flex h-[46px] flex-none items-center justify-center border-b border-shell-border">
        <span className="text-[13px] font-semibold tracking-[-0.01em]">Design Studio</span>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* left rail */}
        <nav
          aria-label="Design Studio views"
          className="flex w-[68px] flex-none flex-col items-center gap-1.5 border-r border-shell-border bg-shell-bg-deep py-3.5"
        >
          {RAIL.map((r) => {
            const Icon = r.icon;
            const on = view === r.id;
            return (
              <button
                key={r.id}
                type="button"
                aria-label={r.label}
                aria-current={on ? "page" : undefined}
                onClick={() => setView(r.id)}
                className={`flex h-[46px] w-[46px] flex-col items-center justify-center gap-0.5 rounded-xl text-[9px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 ${
                  on
                    ? "bg-gradient-to-b from-accent/25 to-transparent text-accent"
                    : "text-shell-text-tertiary hover:bg-white/10 hover:text-shell-text-secondary"
                }`}
              >
                <Icon size={21} />
                {r.label}
              </button>
            );
          })}
          <div className="flex-1" />
          <button
            type="button"
            aria-label="Brand"
            className="flex h-[46px] w-[46px] flex-col items-center justify-center gap-0.5 rounded-xl text-[9px] font-semibold text-shell-text-tertiary transition-colors hover:bg-white/10 hover:text-shell-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
          >
            <Circle size={21} />
            Brand
          </button>
        </nav>

        {/* active surface */}
        <div className="flex min-w-0 flex-1 flex-col">
          {view === "design" && <DesignView />}
          {view === "templates" && <TemplatesView />}
          {view === "elements" && <DesignView />}
          {view === "magic" && <MagicView />}
        </div>
      </div>
    </div>
  );
}
