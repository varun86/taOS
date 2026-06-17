/** Shared prompt seeding between TemplatesView and BuildView. */

export const PROMPT_SEEDED_EVENT = "appstudio:prompt-seeded";

let pendingPrompt: string | null = null;

export function seedBuildPrompt(text: string): void {
  const trimmed = text.trim();
  if (!trimmed) return;
  pendingPrompt = trimmed;
  window.dispatchEvent(new CustomEvent(PROMPT_SEEDED_EVENT, { detail: trimmed }));
}

export function takePendingPrompt(): string | null {
  const prompt = pendingPrompt;
  pendingPrompt = null;
  return prompt;
}