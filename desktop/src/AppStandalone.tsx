import { Suspense, lazy } from "react";
import { getApp } from "./registry/app-registry";
import { InstallPromptBanner } from "./shell/InstallPromptBanner";
import type { ComponentType } from "react";

interface Props {
  appId: string;
}

export function AppStandalone({ appId }: Props) {
  const manifest = getApp(appId);

  // Guard: caller should verify pwa:true before mounting this component.
  if (!manifest) return null;

  const AppComponent = lazy(
    () =>
      manifest.component() as Promise<{ default: ComponentType<{ windowId: string }> }>,
  );

  return (
    <div
      className="h-screen w-screen flex flex-col overflow-hidden"
      style={{ backgroundColor: "var(--color-shell-bg)", paddingTop: "env(safe-area-inset-top, 0px)" }}
    >
      <InstallPromptBanner />
      <Suspense fallback={
        <div className="flex items-center justify-center h-full" style={{ color: "rgba(255,255,255,0.4)" }}>
          Loading...
        </div>
      }>
        <AppComponent windowId={`standalone-${appId}`} />
      </Suspense>
    </div>
  );
}
