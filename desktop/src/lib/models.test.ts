import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchClusterWorkers, fetchCloudProviders } from "./models";

const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("fetchClusterWorkers", () => {
  it("returns workers array on 200 with top-level array body", async () => {
    const workers = [
      { name: "worker-1", url: "http://w1.test" },
      { name: "worker-2", url: "http://w2.test" },
    ];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      json: async () => workers,
    });
    global.fetch = fetchMock;

    const result = await fetchClusterWorkers();
    expect(result).toEqual(workers);

    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/cluster/workers");
    expect(opts.headers.Accept).toBe("application/json");
  });

  it("returns workers array on 200 with { workers } body", async () => {
    const workers = [{ name: "w1", url: "http://w1.test" }];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      json: async () => ({ workers }),
    });
    global.fetch = fetchMock;

    const result = await fetchClusterWorkers();
    expect(result).toEqual(workers);
  });

  it("returns [] on non-ok response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      headers: { get: () => "application/json" },
    });
    expect(await fetchClusterWorkers()).toEqual([]);
  });

  it("returns [] on non-json content type", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "text/html" },
    });
    expect(await fetchClusterWorkers()).toEqual([]);
  });

  it("returns [] when body is not an array and has no workers field", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      json: async () => ({ something: "else" }),
    });
    expect(await fetchClusterWorkers()).toEqual([]);
  });

  it("returns [] on network error", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("network failure"));
    expect(await fetchClusterWorkers()).toEqual([]);
  });
});

describe("fetchCloudProviders", () => {
  it("returns providers array on 200", async () => {
    const providers = [
      { name: "openai", type: "openai", models: [{ id: "gpt-4", name: "GPT-4" }] },
      { name: "ollama-local", type: "ollama", source: "worker:node-1" },
    ];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      json: async () => providers,
    });
    global.fetch = fetchMock;

    const result = await fetchCloudProviders();
    expect(result).toEqual(providers);

    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/providers");
    expect(opts.headers.Accept).toBe("application/json");
  });

  it("returns [] on non-ok response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      headers: { get: () => "application/json" },
    });
    expect(await fetchCloudProviders()).toEqual([]);
  });

  it("returns [] on non-json content type", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "text/plain" },
    });
    expect(await fetchCloudProviders()).toEqual([]);
  });

  it("returns [] when body is not an array", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      json: async () => ({ providers: [] }),
    });
    expect(await fetchCloudProviders()).toEqual([]);
  });

  it("returns [] on network error", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("offline"));
    expect(await fetchCloudProviders()).toEqual([]);
  });
});
