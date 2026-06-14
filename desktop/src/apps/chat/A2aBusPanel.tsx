import { useState, useEffect, useRef, useCallback } from "react";
import { Radio, ChevronRight, Bot } from "lucide-react";

/*
 * Read-only viewer for the external taOSmd A2A coordination bus.
 *
 * The coordination bus is a SEPARATE service (taosmd serve) where cross-product
 * agents (@taOS, @taOSmd, @hermes) coordinate. This is DISTINCT from taOS's own
 * internal per-project a2a channels. Everything here is read-only: the controller
 * exposes a read-only proxy (/api/a2a/bus/*) and this panel only fetches; there
 * is no compose box and no write path.
 *
 * Two pieces live here:
 *   - A2aBusSection: the collapsible sidebar group listing bus channels.
 *   - A2aBusMessageView: the detail pane shown when a bus channel is selected.
 * State is isolated from the project-channel logic in MessagesApp.
 */

const POLL_MS = 8000;

export interface BusChannel {
  channel: string;
  members?: string[];
  message_count?: number;
  created_ts?: number;
  last_ts?: number;
}

export interface BusMessage {
  id: number;
  ts: number;
  from: string;
  body: string;
  thread: string;
  reply_to: number | null;
}

/*
 * Kept local: the existing relative-time helpers in chat/ (AllThreadsList,
 * SearchPanel) and lib/cluster.ts are unexported copies with incompatible
 * shapes -- they call Date.now() internally and return the verbose "Xm ago"
 * form. This view needs a passed-in nowMs (a 60s-ticking state value powers the
 * re-render) and the compact "Xm" form for the tabular timestamp column, so
 * there is no reusable helper to fold into here.
 */
function busRelativeTime(ts: number | undefined, nowMs: number): string {
  if (!ts) return "";
  const ms = ts < 1e12 ? ts * 1000 : ts;
  const mins = Math.floor((nowMs - ms) / 60000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return new Date(ms).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

/**
 * Hook owning the bus channel list + availability, polled every 8s.
 */
export function useBusChannels() {
  const [channels, setChannels] = useState<BusChannel[]>([]);
  const [available, setAvailable] = useState<boolean>(true);
  const [loaded, setLoaded] = useState(false);

  const fetchChannels = useCallback(async () => {
    try {
      const res = await fetch("/api/a2a/bus/channels");
      const data = await res.json();
      setChannels(Array.isArray(data.channels) ? data.channels : []);
      setAvailable(data.available !== false);
    } catch {
      setChannels([]);
      setAvailable(false);
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    fetchChannels();
    const id = setInterval(fetchChannels, POLL_MS);
    return () => clearInterval(id);
  }, [fetchChannels]);

  return { channels, available, loaded };
}

/* ------------------------------------------------------------------ */
/*  Sidebar group                                                      */
/* ------------------------------------------------------------------ */

export function A2aBusSection({
  channels,
  available,
  loaded,
  selected,
  onSelect,
}: {
  channels: BusChannel[];
  available: boolean;
  loaded: boolean;
  selected: string | null;
  onSelect: (channel: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const [nowMs, setNowMs] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNowMs(Date.now()), 60000);
    return () => clearInterval(id);
  }, []);

  // Hide the whole group until the first fetch resolves so it never flashes.
  if (!loaded) return null;

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        aria-controls="a2a-bus-channels"
        className="flex items-center gap-1.5 px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-white/30 hover:text-white/50 transition-colors w-full text-left"
      >
        <ChevronRight
          size={11}
          aria-hidden="true"
          className={`transition-transform ${expanded ? "rotate-90" : ""}`}
        />
        <Radio size={11} aria-hidden="true" />
        Coordination Bus
      </button>
      {expanded && (
        <div id="a2a-bus-channels">
          {!available ? (
            <div className="px-3 py-2">
              <p className="text-[11px] text-white/40">Coordination bus offline</p>
              <p className="text-[10px] text-white/25 mt-0.5">No bus service reachable.</p>
            </div>
          ) : channels.length === 0 ? (
            <div className="px-3 py-1 text-[11px] text-white/20 italic">No channels yet</div>
          ) : (
            channels.map((ch) => (
              <button
                key={ch.channel}
                type="button"
                onClick={() => onSelect(ch.channel)}
                aria-pressed={selected === ch.channel}
                aria-label={`Coordination channel ${ch.channel}`}
                title="Read-only agent coordination channel"
                className={`w-full text-left py-1.5 px-3 text-[13px] flex items-center gap-2 transition-colors ${
                  selected === ch.channel ? "bg-white/10" : "hover:bg-white/5"
                }`}
              >
                <Radio size={14} aria-hidden className="shrink-0 text-white/50" />
                <span className="truncate flex-1">{ch.channel}</span>
                <span className="shrink-0 text-[10px] text-white/30 tabular-nums">
                  {(ch.members?.length ?? 0)} · {busRelativeTime(ch.last_ts, nowMs)}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Detail pane                                                        */
/* ------------------------------------------------------------------ */

export function A2aBusMessageView({ channel }: { channel: string }) {
  const [messages, setMessages] = useState<BusMessage[]>([]);
  const [available, setAvailable] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const fetchMessages = useCallback(async () => {
    try {
      const res = await fetch(
        `/api/a2a/bus/messages?channel=${encodeURIComponent(channel)}&limit=100`,
      );
      const data = await res.json();
      setMessages(Array.isArray(data.messages) ? data.messages : []);
      setAvailable(data.available !== false);
    } catch {
      setMessages([]);
      setAvailable(false);
    } finally {
      setLoaded(true);
    }
  }, [channel]);

  useEffect(() => {
    setLoaded(false);
    fetchMessages();
    const id = setInterval(fetchMessages, POLL_MS);
    return () => clearInterval(id);
  }, [fetchMessages]);

  useEffect(() => {
    const id = setInterval(() => setNowMs(Date.now()), 60000);
    return () => clearInterval(id);
  }, []);

  // Stick to the bottom (newest message) only when the user is already there,
  // so an 8s poll never yanks them away from history they scrolled up to read.
  const nearBottomRef = useRef(true);
  useEffect(() => {
    const el = scrollRef.current;
    if (el && nearBottomRef.current) el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  // Reset stickiness on channel change so a fresh load pins to the bottom.
  useEffect(() => {
    nearBottomRef.current = true;
  }, [channel]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    nearBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }, []);

  return (
    <div className="relative flex-1 flex flex-col min-w-0 h-full">
      {/* header */}
      <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center gap-3 shrink-0">
        <Radio size={16} className="text-white/40" aria-hidden="true" />
        <div className="min-w-0">
          <div className="text-sm font-semibold text-white/90 truncate">{channel}</div>
          <div className="text-[11px] text-white/40">Coordination bus · read-only</div>
        </div>
      </div>

      {/* messages */}
      <div ref={scrollRef} onScroll={handleScroll} className="flex-1 overflow-y-auto px-4 py-3">
        {!loaded ? (
          <div className="h-full flex items-center justify-center text-white/20 text-sm">
            Loading…
          </div>
        ) : !available ? (
          <div className="h-full flex flex-col items-center justify-center text-center gap-2 px-6">
            <Radio size={32} className="text-white/15" aria-hidden="true" />
            <p className="text-sm font-medium text-white/60">Coordination bus offline</p>
            <p className="text-[12px] text-white/30">
              The bus service is not reachable right now.
            </p>
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center gap-2 px-6">
            <Bot size={32} className="text-white/15" aria-hidden="true" />
            <p className="text-sm font-medium text-white/60">No messages yet</p>
            <p className="text-[12px] text-white/30">
              Agent coordination will appear here.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {messages.map((m) => (
              <div key={m.id} className="flex flex-col gap-0.5">
                <div className="flex items-baseline gap-2">
                  <span className="text-[13px] font-semibold text-white/85 truncate">
                    {m.from}
                  </span>
                  <span className="text-[10px] text-white/30 tabular-nums shrink-0">
                    {busRelativeTime(m.ts, nowMs)}
                  </span>
                </div>
                <div className="text-[13px] text-white/75 whitespace-pre-wrap break-words">
                  {m.body}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* read-only footer. Bottom inset keeps it clear of the phone home
          indicator / dock edge; env() is 0 on desktop so layout is unchanged. */}
      <div
        className="px-4 py-2 border-t border-white/[0.06] text-[11px] text-white/35 shrink-0"
        style={{ paddingBottom: "calc(0.5rem + env(safe-area-inset-bottom, 0px))" }}
      >
        Read-only. The coordination bus is managed by the agents.
      </div>
    </div>
  );
}
