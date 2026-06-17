import { Sparkles } from "lucide-react";

const STYLE_CHIPS = ["Bold", "Minimal", "Editorial", "Playful", "Dark", "Corporate"];

const RESULTS: { label: string; gradient: string }[] = [
  {
    label: "Bold, centered",
    gradient:
      "radial-gradient(130% 120% at 20% 12%, #5a6b86, transparent 55%), linear-gradient(150deg, #2c3142, #171a24)",
  },
  {
    label: "Split layout",
    gradient:
      "radial-gradient(130% 120% at 80% 18%, #3d8f7a, transparent 55%), linear-gradient(150deg, #16302a, #0e1c18)",
  },
  {
    label: "Editorial",
    gradient:
      "radial-gradient(130% 120% at 30% 80%, #c98b5b, transparent 55%), linear-gradient(150deg, #2a2018, #15100b)",
  },
];

export function MagicView() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* view header */}
      <div
        className="flex flex-none items-center gap-3 border-b border-shell-border px-[22px]"
        style={{ height: "54px" }}
      >
        <h2 className="text-[17px] font-bold tracking-[-0.02em]">Magic design</h2>
        <span className="text-[12px] text-shell-text-tertiary">Describe it, get a full layout</span>
      </div>

      {/* scrollable body */}
      <div className="flex flex-1 flex-col items-center overflow-auto px-[26px] pb-[26px] pt-[26px]">
        {/* hero */}
        <div className="mb-6 w-full max-w-[640px] text-center">
          <h3 className="text-[24px] font-extrabold tracking-[-0.02em]">
            Describe the design you need.
          </h3>
          <p className="mt-2 text-[13.5px] leading-[1.5] text-shell-text-secondary">
            An agent on your cluster lays it out with your brand kit, fonts, and colors. Pick one and keep editing on the canvas.
          </p>
        </div>

        {/* prompt bar */}
        <div className="mb-[26px] flex w-full max-w-[640px] gap-2.5">
          <div className="flex-1 rounded-[14px] border border-shell-border-strong bg-shell-surface px-4 py-3.5 text-[13.5px] text-shell-text-tertiary">
            a launch poster for taOS Studios, bold, dark, confident...
          </div>
          <button
            type="button"
            className="flex items-center gap-2 rounded-[14px] px-[22px] py-3.5 text-[14px] font-bold text-white"
            style={{
              background: "linear-gradient(135deg,#a9b0c2,#8b92a3)",
              border: "none",
            }}
          >
            <Sparkles size={17} />
            Generate
          </button>
        </div>

        {/* style chips */}
        <div className="mb-6 flex w-full max-w-[640px] flex-wrap gap-2">
          {STYLE_CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              className="rounded-full border border-shell-border bg-shell-surface px-[14px] py-[7px] text-[12px] font-semibold text-shell-text-secondary transition-colors hover:border-shell-border-strong hover:text-shell-text"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* generated result tiles */}
        <div className="grid w-full max-w-[760px] grid-cols-3 gap-[14px]">
          {RESULTS.map(({ label, gradient }) => (
            <div
              key={label}
              className="relative cursor-pointer overflow-hidden rounded-[12px] border border-shell-border transition-all hover:-translate-y-[3px]"
              style={{ aspectRatio: "0.8", background: gradient }}
            >
              <div
                className="absolute bottom-0 left-0 right-0 px-[11px] py-[9px] text-[11px] text-white"
                style={{ background: "linear-gradient(transparent, rgba(0,0,0,0.6))" }}
              >
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
