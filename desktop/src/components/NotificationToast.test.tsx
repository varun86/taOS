import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { NotificationToasts } from "./NotificationToast";

const mockDismiss = vi.fn();
const mockNotifications: Array<{
  id: string;
  source: string;
  title: string;
  body: string;
  level: "info" | "success" | "warning" | "error";
  read: boolean;
  timestamp: number;
}> = [];

vi.mock("@/stores/notification-store", () => ({
  useNotificationStore: (selector: (state: { notifications: typeof mockNotifications; dismiss: typeof mockDismiss }) => unknown) =>
    selector({ notifications: mockNotifications, dismiss: mockDismiss }),
}));

vi.mock("@/stores/process-store", () => ({
  useProcessStore: () => ({ openWindow: vi.fn() }),
}));

vi.mock("@/registry/app-registry", () => ({
  getApp: vi.fn(),
}));

describe("NotificationToasts", () => {
  it("renders nothing when there are no notifications", () => {
    const { container } = render(<NotificationToasts />);
    expect(container.querySelector("[aria-label='Notifications']")?.children.length).toBe(0);
  });

  it("renders a notification toast with title and body", () => {
    mockNotifications.length = 0;
    mockNotifications.push({
      id: "test-1",
      source: "system",
      title: "Update available",
      body: "A new version of taOS is ready to install.",
      level: "info",
      read: false,
      timestamp: Date.now(),
    });
    render(<NotificationToasts />);
    expect(screen.getByText("Update available")).toBeInTheDocument();
    expect(screen.getByText("A new version of taOS is ready to install.")).toBeInTheDocument();
  });

  it("calls dismiss when the close button is clicked", async () => {
    mockNotifications.length = 0;
    mockNotifications.push({
      id: "test-2",
      source: "system",
      title: "Restart required",
      body: "Please restart to apply changes.",
      level: "warning",
      read: false,
      timestamp: Date.now(),
    });
    mockDismiss.mockClear();
    render(<NotificationToasts />);
    fireEvent.click(screen.getByRole("button", { name: /dismiss notification/i }));
    await waitFor(() => expect(mockDismiss).toHaveBeenCalledWith("test-2"));
  });
});
