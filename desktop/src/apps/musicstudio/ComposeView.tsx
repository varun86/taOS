import { Sparkles, Play } from "lucide-react";

const STYLE_CHIPS = ["Lo-fi", "Cinematic", "House", "Ambient", "Drum and bass", "Hip-hop"];

interface GeneratedResult {
  bpm: number;
  duration: string;
  bars: number[];
}

const RESULTS: GeneratedResult[] = [
  { bpm: 92, duration: "0:48", bars: [30, 60, 45, 80, 50, 70, 40, 90, 55, 65, 35, 75, 50, 60] },
  { bpm: 90, duration: "1:02", bars: [50, 40, 70, 55, 85, 45, 60, 50, 75, 40, 65, 55, 80, 45] },
  { bpm: 94, duration: "0:54", bars: [40, 55, 50, 65, 45, 75, 55, 60, 50, 70, 45, 80, 50, 60] },
];

export function ComposeView() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* view header */}
      <div
        className="flex flex-none items-center gap-3 border-b border-shell-border px-[22px]"
        style={{ height: "54px" }}
      >
        <h2 className="text-[17px] font-bold tracking-[-0.02em]">Compose</h2>
        <span className="text-[12px] text-shell-text-tertiary">
          Describe a track, get a full arrangement
        </span>
      </div>

      <div className="flex flex-1 flex-col items-center overflow-auto p-[26px]">
        {/* hero */}
        <div className="mb-[22px] max-w-[620px] text-center">
          <h3 className="text-[23px] font-extrabold tracking-[-0.02em]">
            Hum it, or just describe it.
          </h3>
          <p className="mt-2 text-[13.5px] leading-[1.5] text-shell-text-secondary">
            An agent on your cluster writes a multi-track arrangement you can open in the studio
            and edit note by note. Apache-licensed models, nothing leaves your network.
          </p>
        </div>

        {/* prompt bar */}
        <div className="mb-3.5 flex w-full max-w-[620px] gap-2.5">
          <div className="flex-1 rounded-[14px] border border-shell-border bg-shell-surface px-4 py-3.5 text-[13.5px] text-shell-text-tertiary">
            a warm lo-fi beat, 90 bpm, dusty drums, rhodes chords, vinyl crackle...
          </div>
          <button
            type="button"
            className="flex cursor-pointer items-center gap-2 rounded-[14px] border-0 px-[22px] text-[14px] font-bold text-white"
            style={{
              background: "linear-gradient(135deg, var(--color-accent-strong, #a9b0c2), var(--color-accent, #8b92a3))",
            }}
          >
            <Sparkles size={17} />
            Generate
          </button>
        </div>

        {/* style chips */}
        <div className="mb-[26px] flex flex-wrap justify-center gap-2">
          {STYLE_CHIPS.map((chip, i) => (
            <button
              key={chip}
              type="button"
              className={`rounded-full border px-3.5 py-[7px] text-[11.5px] font-semibold ${
                i === 0
                  ? "border-accent bg-accent/20 text-accent"
                  : "border-shell-border bg-shell-surface text-shell-text-secondary"
              }`}
            >
              {chip}
            </button>
          ))}
        </div>

        {/* generated results */}
        <div className="flex w-full max-w-[660px] flex-col gap-[11px]">
          {RESULTS.map((result, i) => (
            <div
              key={i}
              className="flex cursor-pointer items-center gap-3.5 rounded-[14px] border border-shell-border bg-shell-surface px-[15px] py-[13px] hover:bg-shell-surface-active"
            >
              <div
                className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-[11px] text-white"
                style={{ background: "linear-gradient(135deg, var(--color-accent-strong, #a9b0c2), var(--color-accent, #8b92a3))" }}
              >
                <Play size={16} fill="currentColor" />
              </div>

              <div className="flex flex-1 items-center gap-[2px]" style={{ height: "30px" }}>
                {result.bars.map((h, bi) => (
                  <span
                    key={bi}
                    className="flex-1 rounded-[1px] opacity-55"
                    style={{ height: `${h}%`, background: "var(--color-shell-text-tertiary, rgba(255,255,255,0.40))" }}
                  />
                ))}
              </div>

              <span className="whitespace-nowrap text-[11px] text-shell-text-tertiary">
                {result.bpm} BPM - {result.duration}
              </span>
              <span className="text-[11.5px] font-bold text-accent">Open</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
