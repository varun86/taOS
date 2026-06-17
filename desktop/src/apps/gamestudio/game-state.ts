/** Shared create -> play state between CreateView and PlayView. */

import type { BuildStep, Template } from "./types";

export const GAME_CREATED_EVENT = "gamestudio:game-created";

let pendingPrompt: string | null = null;
let pendingSteps: BuildStep[] | null = null;
let pendingTemplate: Template | null = null;

export function seedCreatedGame(
  template: Template,
  prompt: string,
  steps: BuildStep[],
): void {
  pendingTemplate = template;
  pendingPrompt = prompt.trim() || null;
  pendingSteps = steps;
  window.dispatchEvent(
    new CustomEvent(GAME_CREATED_EVENT, { detail: { template, prompt, steps } }),
  );
}

export function takeCreatedGame(): {
  template: Template | null;
  prompt: string | null;
  steps: BuildStep[] | null;
} {
  const snapshot = {
    template: pendingTemplate,
    prompt: pendingPrompt,
    steps: pendingSteps,
  };
  pendingTemplate = null;
  pendingPrompt = null;
  pendingSteps = null;
  return snapshot;
}

export function peekCreatedSteps(): BuildStep[] | null {
  return pendingSteps;
}