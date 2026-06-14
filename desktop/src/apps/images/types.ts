/* ------------------------------------------------------------------ */
/*  Images Studio — shared types                                       */
/* ------------------------------------------------------------------ */

/** A generated image as surfaced by /api/images (list) and the result
 *  of /api/images/generate. Mirrors the shape the legacy ImagesApp mapped. */
export interface GeneratedImage {
  id: string;
  url: string;
  prompt: string;
  model: string;
  size: number | string;
  steps: number;
  seed: number;
  guidance: number;
  backend?: string;
  createdAt: string;
}

export interface ModelVariant {
  id: string;
  name: string;
  format?: string;
  size_mb: number;
  min_ram_mb?: number;
  backend?: string[];
  downloaded?: boolean;
  compatibility: "green" | "yellow" | "red";
  download_url?: string;
}

export interface ImageModel {
  id: string;
  name: string;
  description?: string;
  capabilities: string[];
  variants: ModelVariant[];
  has_downloaded_variant?: boolean;
}

/** Parameters posted to /api/images/generate. */
export interface GenerateParams {
  prompt: string;
  model: string;
  variant: string;
  size: string;
  steps: number;
  seed: number;
  guidance_scale: number;
}

export type StudioView = "create" | "library" | "edit";

export type GenerateMode = "single" | "batch";

export type LibraryFilter = "all" | "flux" | "sdxl";

/** Edit tools. Client-side ops are real; generative ops are staged. */
export type EditTool =
  | "adjust"
  | "erase"
  | "inpaint"
  | "removebg"
  | "extend"
  | "upscale"
  | "vary";

/** The generative tools have no backend yet and are gated with a
 *  "Coming soon" affordance. "adjust" is real (CSS-filter based). */
export const STAGED_TOOLS: ReadonlySet<EditTool> = new Set<EditTool>([
  "erase",
  "inpaint",
  "removebg",
  "extend",
  "upscale",
  "vary",
]);

export const SIZE_OPTIONS = [256, 512, 768, 1024] as const;

export const STYLE_CHIPS = [
  "Storybook",
  "Photoreal",
  "Watercolor",
  "3D",
  "Anime",
] as const;
