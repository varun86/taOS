import { useState, useMemo } from "react";
import {
  SlidersHorizontal,
  Eraser,
  Sparkles,
  Scissors,
  Maximize2,
  Expand,
  Shuffle,
  Undo2,
  Check,
  ImageIcon,
} from "lucide-react";
import { Slider, Chip, GroupLabel } from "./controls";
import { STAGED_TOOLS, type EditTool, type GeneratedImage } from "./types";

/* ------------------------------------------------------------------ */
/*  EditView — tool rail + canvas + tool options + action bar          */
/*                                                                     */
/*  Adjust is a REAL client-side op (CSS filters). All generative ops   */
/*  (erase/inpaint/removebg/extend/upscale/vary) have no backend yet    */
/*  and are gated with a "Coming soon" affordance — Apply is disabled.  */
/* ------------------------------------------------------------------ */

interface ToolDef {
  id: EditTool;
  label: string;
  icon: typeof SlidersHorizontal;
  title: string;
  desc: string;
}

const TOOLS: ToolDef[] = [
  {
    id: "adjust",
    label: "Adjust",
    icon: SlidersHorizontal,
    title: "Adjust",
    desc: "Tune brightness, contrast and saturation. Applied live, on-device.",
  },
  {
    id: "erase",
    label: "Erase",
    icon: Eraser,
    title: "Magic Eraser",
    desc: "Brush over anything you want gone. taOS fills the area to match the surroundings.",
  },
  {
    id: "inpaint",
    label: "Inpaint",
    icon: Sparkles,
    title: "Inpaint",
    desc: "Paint a mask, then describe what should appear there instead.",
  },
  {
    id: "removebg",
    label: "Remove BG",
    icon: Scissors,
    title: "Remove background",
    desc: "Cut the subject out and drop a transparent background, on-device.",
  },
  {
    id: "extend",
    label: "Extend",
    icon: Expand,
    title: "Extend / outpaint",
    desc: "Grow the canvas and let taOS paint in the new edges.",
  },
  {
    id: "upscale",
    label: "Upscale",
    icon: Maximize2,
    title: "Upscale",
    desc: "Increase resolution and sharpen detail without artefacts.",
  },
  {
    id: "vary",
    label: "Vary",
    icon: Shuffle,
    title: "Variations",
    desc: "Generate fresh takes that keep the spirit of this image.",
  },
];

export interface EditViewProps {
  image: GeneratedImage | null;
  onApplyAdjust: (filterCss: string) => void;
}

const DEFAULT_ADJUST = { brightness: 100, contrast: 100, saturation: 100 };

export function EditView({ image, onApplyAdjust }: EditViewProps) {
  const [tool, setTool] = useState<EditTool>("adjust");
  const [adjust, setAdjust] = useState(DEFAULT_ADJUST);
  const [brush, setBrush] = useState(54);
  const [replacePrompt, setReplacePrompt] = useState("");
  const [eraseMode, setEraseMode] = useState<"erase" | "replace">("erase");

  const filterCss = useMemo(
    () =>
      `brightness(${adjust.brightness}%) contrast(${adjust.contrast}%) saturate(${adjust.saturation}%)`,
    [adjust],
  );

  const def = TOOLS.find((t) => t.id === tool) ?? TOOLS[0]!;
  const staged = STAGED_TOOLS.has(tool);
  const dirty =
    tool === "adjust" &&
    (adjust.brightness !== 100 ||
      adjust.contrast !== 100 ||
      adjust.saturation !== 100);

  function reset() {
    if (tool === "adjust") setAdjust(DEFAULT_ADJUST);
    setReplacePrompt("");
  }

  function apply() {
    if (tool === "adjust") onApplyAdjust(filterCss);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* view header */}
      <div className="flex h-[54px] flex-none items-center gap-3 border-b border-shell-border px-[22px]">
        <h2 className="text-[17px] font-bold tracking-[-0.02em]">Edit</h2>
        <span className="text-[12px] text-shell-text-tertiary truncate">
          {image
            ? `${image.prompt.split(" ").slice(0, 4).join(" ")} · ${
                typeof image.size === "number"
                  ? `${image.size} × ${image.size}`
                  : image.size
              }`
            : "No image selected"}
        </span>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* tool rail */}
        <div
          className="flex w-[78px] flex-none flex-col items-center gap-1 border-r border-shell-border bg-shell-bg-deep py-3"
          role="tablist"
          aria-label="Edit tools"
        >
          {TOOLS.map((t) => {
            const Icon = t.icon;
            const on = t.id === tool;
            return (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={on}
                aria-label={t.label}
                onClick={() => setTool(t.id)}
                className={`flex w-[62px] flex-col items-center gap-1 rounded-xl py-2.5 text-[9.5px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 ${
                  on
                    ? "bg-gradient-to-b from-accent/25 to-transparent text-accent"
                    : "text-shell-text-tertiary hover:bg-white/10 hover:text-shell-text-secondary"
                }`}
              >
                <Icon size={20} />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* canvas */}
        <div className="relative flex min-w-0 flex-1 items-center justify-center p-[22px]">
          {image && image.url ? (
            <div className="relative overflow-hidden rounded-2xl border border-shell-border shadow-[var(--shadow-window)]">
              <img
                src={image.url}
                alt={image.prompt}
                style={tool === "adjust" ? { filter: filterCss } : undefined}
                className="block max-h-[430px] w-auto"
              />
              {/* brush-mask overlay preview for staged masking tools */}
              {(tool === "erase" || tool === "inpaint") && (
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute left-[46%] top-[34%] rounded-full border-2 border-dashed border-accent bg-accent/30 mix-blend-screen"
                  style={{ width: brush * 2.4, height: brush * 1.9 }}
                />
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-shell-text-tertiary">
              <ImageIcon size={40} className="opacity-30" />
              <p className="text-sm">Pick an image from the Library to edit</p>
            </div>
          )}
        </div>

        {/* options panel */}
        <div className="flex w-[286px] flex-none flex-col gap-[18px] overflow-auto border-l border-shell-border p-[18px]">
          <div className="flex items-center gap-2.5 text-[15px] font-bold tracking-[-0.01em]">
            <def.icon size={18} className="text-accent" />
            {def.title}
            {staged && (
              <span className="ml-auto rounded-full border border-shell-border bg-shell-surface px-2 py-0.5 text-[9.5px] font-semibold uppercase tracking-wide text-shell-text-tertiary">
                Soon
              </span>
            )}
          </div>
          <p className="-mt-2 text-[12px] leading-relaxed text-shell-text-secondary">
            {def.desc}
          </p>

          {tool === "adjust" && (
            <>
              <Slider
                id="edit-brightness"
                label="Brightness"
                value={adjust.brightness}
                min={0}
                max={200}
                display={`${adjust.brightness}%`}
                onChange={(v) =>
                  setAdjust((a) => ({ ...a, brightness: Math.round(v) }))
                }
              />
              <Slider
                id="edit-contrast"
                label="Contrast"
                value={adjust.contrast}
                min={0}
                max={200}
                display={`${adjust.contrast}%`}
                onChange={(v) =>
                  setAdjust((a) => ({ ...a, contrast: Math.round(v) }))
                }
              />
              <Slider
                id="edit-saturation"
                label="Saturation"
                value={adjust.saturation}
                min={0}
                max={200}
                display={`${adjust.saturation}%`}
                onChange={(v) =>
                  setAdjust((a) => ({ ...a, saturation: Math.round(v) }))
                }
              />
            </>
          )}

          {(tool === "erase" || tool === "inpaint") && (
            <>
              <Slider
                id="edit-brush"
                label="Brush size"
                value={brush}
                min={10}
                max={120}
                display={String(brush)}
                onChange={(v) => setBrush(Math.round(v))}
              />
              <div>
                <GroupLabel>
                  {tool === "inpaint" ? "Replace with" : "Or replace with"}
                </GroupLabel>
                <input
                  type="text"
                  value={replacePrompt}
                  onChange={(e) => setReplacePrompt(e.target.value)}
                  placeholder="optional prompt"
                  aria-label="Replacement prompt"
                  className="w-full rounded-xl border border-shell-border bg-shell-surface px-3 py-2.5 text-[12.5px] text-shell-text placeholder:text-shell-text-tertiary focus-visible:outline-none focus-visible:border-accent/40 focus-visible:ring-2 focus-visible:ring-accent/20"
                />
              </div>
              {tool === "erase" && (
                <div>
                  <GroupLabel>Mode</GroupLabel>
                  <div className="flex gap-[7px]">
                    <Chip
                      label="Erase"
                      on={eraseMode === "erase"}
                      onClick={() => setEraseMode("erase")}
                    />
                    <Chip
                      label="Replace"
                      on={eraseMode === "replace"}
                      onClick={() => setEraseMode("replace")}
                    />
                  </div>
                </div>
              )}
            </>
          )}

          {staged && tool !== "erase" && tool !== "inpaint" && (
            <p className="rounded-xl border border-shell-border bg-shell-surface px-3 py-2.5 text-[12px] leading-relaxed text-shell-text-tertiary">
              This on-device tool is coming soon.
            </p>
          )}
        </div>
      </div>

      {/* action bar */}
      <div className="flex flex-none items-center gap-2.5 border-t border-shell-border bg-shell-bg-deep px-[22px] py-3">
        <button
          type="button"
          onClick={reset}
          disabled={tool === "adjust" ? !dirty : !staged && !replacePrompt}
          aria-label="Undo changes"
          className="flex h-[42px] items-center gap-1.5 rounded-xl border border-transparent px-4 text-[12.5px] font-semibold text-shell-text-tertiary transition-colors hover:bg-white/10 disabled:pointer-events-none disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <Undo2 size={15} />
          Undo
        </button>
        <button
          type="button"
          onClick={reset}
          aria-label="Reset"
          className="flex h-[42px] items-center rounded-xl border border-transparent px-4 text-[12.5px] font-semibold text-shell-text-tertiary transition-colors hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          Reset
        </button>
        <button
          type="button"
          onClick={apply}
          disabled={!image || staged || (tool === "adjust" && !dirty)}
          aria-label={staged ? "Apply (coming soon)" : "Apply changes"}
          title={staged ? "Coming soon" : undefined}
          className="ml-auto flex h-[42px] items-center gap-1.5 rounded-xl border border-transparent bg-gradient-to-br from-accent to-accent/70 px-5 text-[12.5px] font-semibold text-white shadow-lg shadow-accent/20 transition-all hover:-translate-y-0.5 hover:brightness-105 disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <Check size={16} />
          {staged ? "Coming soon" : "Apply"}
        </button>
      </div>
    </div>
  );
}
