import { Suspense, lazy, useMemo } from "react";
import { getApp } from "@/registry/app-registry";

interface Props {
  appId: string;
  windowId: string;
  props?: Record<string, unknown>;
  launchNonce?: number;
}

export function WindowContent({ appId, windowId, props, launchNonce = 0 }: Props) {
  const app = getApp(appId);
  const LazyComponent = useMemo(() => {
    if (!app) return null;
    return lazy(app.component);
  }, [app]);

  if (!LazyComponent) {
    return (
      <div className="flex items-center justify-center h-full text-shell-text-secondary">
        Unknown app: {appId}
      </div>
    );
  }

  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-full text-shell-text-tertiary">
          Loading...
        </div>
      }
    >
      <LazyComponent key={`${windowId}:${launchNonce}`} windowId={windowId} {...(props ?? {})} />
    </Suspense>
  );
}
