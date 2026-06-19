import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { InstallHelperPanel } from "./InstallHelperPanel";

describe("InstallHelperPanel", () => {
  beforeEach(() => {
    Object.defineProperty(window, "location", {
      value: { origin: "http://localhost:3000" },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders with appId and appName in heading", () => {
    render(
      <InstallHelperPanel appId="myapp" appName="My App" onClose={vi.fn()} />
    );
    expect(screen.getByText("Install My App")).toBeInTheDocument();
  });

  it("shows the correct install URL", () => {
    render(
      <InstallHelperPanel appId="myapp" appName="My App" onClose={vi.fn()} />
    );
    expect(
      screen.getByDisplayValue("http://localhost:3000/app.html?app=myapp")
    ).toBeInTheDocument();
  });

  it("Copy button writes URL to clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText },
      userAgent: "Chrome",
      platform: "Win32",
      maxTouchPoints: 0,
    });

    render(
      <InstallHelperPanel appId="myapp" appName="My App" onClose={vi.fn()} />
    );

    fireEvent.click(screen.getByText("Copy"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("/app.html?app=myapp")
    );
  });

  it("onClose fires when Done button is clicked", () => {
    const onClose = vi.fn();
    render(
      <InstallHelperPanel appId="myapp" appName="My App" onClose={onClose} />
    );
    fireEvent.click(screen.getByText("Done"));
    expect(onClose).toHaveBeenCalled();
  });
});
