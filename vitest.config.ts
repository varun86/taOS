import path from "path";

export default {
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [path.resolve(__dirname, "desktop/vitest.setup.ts")],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, "desktop/src") },
  },
};
