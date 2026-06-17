import {
  Sparkles,
  AlignLeft,
  AlignCenter,
  Pencil,
  Scissors,
  ArrowRight,
  AlignJustify,
} from "lucide-react";

const AI_OPTIONS: { label: string; desc: string; Icon: typeof Sparkles }[] = [
  { label: "Rewrite", desc: "Clearer, same meaning", Icon: Pencil },
  { label: "Shorten", desc: "Tighten the selection", Icon: Scissors },
  { label: "Continue writing", desc: "Pick up where you left off", Icon: ArrowRight },
  { label: "Change tone", desc: "Friendly, formal, punchy", Icon: AlignJustify },
];

export function WriteView() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* formatting toolbar */}
      <div className="flex h-[46px] flex-none items-center gap-1.5 border-b border-shell-border bg-shell-bg-deep px-4">
        <div className="flex h-8 items-center gap-2 rounded-lg border border-shell-border bg-shell-surface px-3 text-[12px] font-semibold text-shell-text-secondary">
          Sohne <span className="text-shell-text-tertiary">&#9662;</span>
        </div>
        <div className="mx-1.5 h-5 w-px bg-shell-border" />
        <button
          type="button"
          aria-label="Bold"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[14px] font-extrabold text-shell-text-secondary hover:bg-shell-surface-active hover:text-shell-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          B
        </button>
        <button
          type="button"
          aria-label="Italic"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[14px] italic text-shell-text-secondary hover:bg-shell-surface-active hover:text-shell-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          I
        </button>
        <button
          type="button"
          aria-label="Underline"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[14px] underline text-shell-text-secondary hover:bg-shell-surface-active hover:text-shell-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          U
        </button>
        <div className="mx-1.5 h-5 w-px bg-shell-border" />
        <button
          type="button"
          aria-label="Align left"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-shell-text-secondary hover:bg-shell-surface-active hover:text-shell-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <AlignLeft size={16} />
        </button>
        <button
          type="button"
          aria-label="Align center"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-shell-text-secondary hover:bg-shell-surface-active hover:text-shell-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <AlignCenter size={16} />
        </button>
        <div className="ml-auto" />
        <button
          type="button"
          className="flex h-8 items-center gap-1.5 rounded-[9px] bg-gradient-to-br from-accent to-accent/70 px-3.5 text-[12px] font-bold text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <Sparkles size={14} />
          Assist
        </button>
      </div>

      {/* document area + AI panel */}
      <div className="flex min-h-0 flex-1">
        {/* document scroll area */}
        <div className="flex flex-1 justify-center overflow-auto bg-shell-bg-deep px-0 py-7">
          <div
            className="min-h-[660px] w-[540px] rounded-[4px] px-14 py-[52px]"
            style={{
              background: "#f7f7f9",
              boxShadow: "0 16px 40px -14px rgba(0,0,0,0.5)",
              color: "#23232a",
            }}
          >
            <h1
              className="mb-1.5 font-extrabold leading-tight tracking-tight"
              style={{ fontSize: 27, letterSpacing: "-0.02em" }}
            >
              taOS Studios launch note
            </h1>
            <p className="mb-5 text-[12px]" style={{ color: "#5a5a66" }}>
              Draft &middot; updated just now
            </p>
            <p className="mb-3 text-[13.5px] leading-[1.75]" style={{ color: "#33333c" }}>
              taOS now ships a family of creative studios, each a focused workspace that runs
              entirely on hardware you already own.{" "}
              <span
                className="rounded-[3px] px-0.5 py-px"
                style={{ background: "rgba(139,146,163,0.28)" }}
              >
                Whether you are building a business, a hobby project, or something just for the
                house
              </span>
              , there is a studio with the tools you need.
            </p>
            <h2
              className="mb-2 font-bold"
              style={{ fontSize: 16, marginTop: 18, color: "#23232a" }}
            >
              What is ready today
            </h2>
            <p className="mb-3 text-[13.5px] leading-[1.75]" style={{ color: "#33333c" }}>
              Images Studio and Game Studio are available now. Coding Studio is rolling out, with
              Design, Music, App, and Office studios close behind. Each one installs from the Store
              in a single click.
            </p>
            <p className="mb-3 text-[13.5px] leading-[1.75]" style={{ color: "#33333c" }}>
              Everything runs offline by default, on your cluster, with nothing leaving your network
              unless you choose to share it.
            </p>
          </div>
        </div>

        {/* AI panel */}
        <aside className="flex w-[262px] flex-none flex-col gap-3 border-l border-shell-border bg-shell-bg p-[18px]">
          <div className="flex items-center gap-2 text-[14px] font-bold">
            <Sparkles size={16} className="text-accent" />
            Assist
          </div>

          {AI_OPTIONS.map(({ label, desc, Icon }) => (
            <button
              key={label}
              type="button"
              className="flex items-center gap-3 rounded-xl border border-shell-border bg-shell-surface px-3 py-[11px] text-left transition-colors hover:border-shell-border-strong hover:bg-shell-surface-active focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
            >
              <Icon size={16} className="shrink-0 text-accent" />
              <div>
                <div className="text-[12.5px] font-semibold text-shell-text">{label}</div>
                <div className="text-[10.5px] text-shell-text-tertiary">{desc}</div>
              </div>
            </button>
          ))}

          <div className="mt-auto min-h-[70px] rounded-xl border border-shell-border-strong bg-shell-surface p-3 text-[12px] text-shell-text-tertiary">
            Ask for any change to the selected paragraph&hellip;
          </div>
        </aside>
      </div>
    </div>
  );
}
