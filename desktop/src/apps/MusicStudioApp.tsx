import { useState } from "react";
import { LayoutList, Sparkles, Music2, LayoutGrid, Download } from "lucide-react";
import { StudioView } from "./musicstudio/StudioView";
import { ComposeView } from "./musicstudio/ComposeView";
import { SoundsView } from "./musicstudio/SoundsView";

type MusicView = "studio" | "compose" | "sounds" | "mixer" | "export";

const RAIL_MAIN: { id: MusicView; label: string; icon: typeof LayoutList }[] = [
  { id: "studio", label: "Studio", icon: LayoutList },
  { id: "compose", label: "Compose", icon: Sparkles },
  { id: "sounds", label: "Sounds", icon: Music2 },
  { id: "mixer", label: "Mixer", icon: LayoutGrid },
];

export function MusicStudioApp({ windowId: _windowId }: { windowId: string }) {
  const [view, setView] = useState<MusicView>("studio");

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-shell-bg text-shell-text select-none">
      {/* title strip */}
      <div className="flex h-[46px] flex-none items-center justify-center border-b border-shell-border">
        <span className="text-[13px] font-semibold tracking-[-0.01em]">Music Studio</span>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* left rail */}
        <nav
          aria-label="Music Studio views"
          className="flex w-[68px] flex-none flex-col items-center gap-1.5 border-r border-shell-border bg-shell-bg-deep py-3.5"
        >
          {RAIL_MAIN.map((r) => {
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
            aria-label="Export"
            onClick={() => setView("export")}
            className={`flex h-[46px] w-[46px] flex-col items-center justify-center gap-0.5 rounded-xl text-[9px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 ${
              view === "export"
                ? "bg-gradient-to-b from-accent/25 to-transparent text-accent"
                : "text-shell-text-tertiary hover:bg-white/10 hover:text-shell-text-secondary"
            }`}
          >
            <Download size={21} />
            Export
          </button>
        </nav>

        {/* active surface */}
        <div className="flex min-w-0 flex-1 flex-col">
          {view === "studio" && <StudioView />}
          {view === "compose" && <ComposeView />}
          {view === "sounds" && <SoundsView />}
          {view === "mixer" && (
            <div className="flex flex-1 items-center justify-center text-shell-text-secondary text-[13px]">
              Mixer coming soon
            </div>
          )}
          {view === "export" && (
            <div className="flex flex-1 items-center justify-center text-shell-text-secondary text-[13px]">
              Export coming soon
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
