/** Stream NDJSON deltas from POST /api/taos-agent/chat (same pattern as TaosAssistantPanel). */

export async function streamTaosAgentChat(
  messages: { role: string; content: string }[],
  onDelta: (delta: string) => void,
  onError: (message: string) => void,
  opts?: { signal?: AbortSignal },
): Promise<void> {
  const resp = await fetch("/api/taos-agent/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal: opts?.signal,
  });

  if (!resp.ok || !resp.body) {
    const raw = await resp.text().catch(() => "");
    let message = raw.trim();
    if (message.startsWith("{")) {
      try {
        const parsed = JSON.parse(message) as { error?: string };
        if (parsed.error?.trim()) message = parsed.error.trim();
      } catch {
        // keep raw text fallback
      }
    }
    onError(message || `Request failed (${resp.status})`);
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  const flushLines = (lines: string[]) => {
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const obj = JSON.parse(line) as { error?: string; delta?: string };
        if (obj.error) onError(String(obj.error));
        else if (obj.delta) onDelta(obj.delta);
      } catch {
        // skip malformed NDJSON
      }
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    flushLines(lines);
  }

  buf += decoder.decode();
  if (buf.trim()) flushLines([buf]);
}