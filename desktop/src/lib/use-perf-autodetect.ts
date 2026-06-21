import { useEffect } from "react";
import { useThemeStore } from "@/stores/theme-store";

const KEY = "taos-reduce-effects";
// Frames-per-second below this on first load means the GPU is struggling with
// the full effects, so we turn them off automatically. Comfortably below 60 so
// a healthy machine never trips it, but high enough to catch a laggy low-end GPU.
const FPS_THRESHOLD = 40;
const PROBE_MS = 1000;

/**
 * First-run performance auto-detect (#58). When the user has made no explicit
 * Reduce-effects choice yet, measure the frame rate for ~1s and enable Reduce
 * effects if the device is struggling, so low-end hardware is smooth out of the
 * box. An explicit choice (on/off) is always honored and never overridden; a
 * capable machine is left untouched (and simply re-probed on the next load).
 */
export function usePerfAutoDetect(): void {
  const setReduceEffects = useThemeStore((s) => s.setReduceEffects);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(KEY);
    } catch {
      // localStorage unavailable: skip the probe, leave effects on.
      return;
    }
    if (stored === "on" || stored === "off") return; // user already chose

    if (typeof performance === "undefined" || typeof requestAnimationFrame === "undefined") {
      return;
    }

    let frames = 0;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      frames += 1;
      if (now - start < PROBE_MS) {
        raf = requestAnimationFrame(tick);
        return;
      }
      const fps = (frames * 1000) / (now - start);
      // Only persist when we turn effects OFF (a low-end device benefits from
      // the no-flash fast path on the next load). A capable machine stays
      // unset so it re-probes and adapts if the hardware ever changes.
      if (fps < FPS_THRESHOLD) setReduceEffects(true);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [setReduceEffects]);
}
