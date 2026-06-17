/** Stream NDJSON deltas from POST /api/taos-agent/chat (same pattern as TaosAssistantPanel). */

export async function streamTaosAgentChat(
  messages: { role: string; content: string }[],
  onDelta: (delta: string) => void,
  onError: (message: string) => void,
): Promise<void> {
  const resp = await fetch("/api/taos-agent/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!resp.ok || !resp.body) {
    onError(await resp.text().catch(() => "Unknown error"));
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
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
  }
}