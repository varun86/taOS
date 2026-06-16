import {
  Sparkles,
  Folder,
  FileText,
  ClipboardCheck,
  Check,
  Circle,
  ChevronDown,
  Play,
} from "lucide-react";

const CODE_LINES = [
  {
    n: 1,
    jsx: (
      <>
        <span style={{ color: "#8e9cd6" }}>import</span>
        {" { useTodos } "}
        <span style={{ color: "#8e9cd6" }}>from</span>
        {" "}
        <span style={{ color: "#8fb89a" }}>{"'./useTodos'"}</span>
      </>
    ),
  },
  {
    n: 2,
    jsx: (
      <>
        <span style={{ color: "#8e9cd6" }}>import</span>
        {" { TodoList } "}
        <span style={{ color: "#8e9cd6" }}>from</span>
        {" "}
        <span style={{ color: "#8fb89a" }}>{"'./TodoList'"}</span>
      </>
    ),
  },
  {
    n: 3,
    jsx: (
      <span style={{ color: "rgba(255,255,255,0.32)" }}>
        {"// added by taOS - persists to localStorage"}
      </span>
    ),
  },
  { n: 4, jsx: <></> },
  {
    n: 5,
    jsx: (
      <>
        <span style={{ color: "#8e9cd6" }}>export default function</span>
        {" "}
        <span style={{ color: "#9fb0d2" }}>App</span>
        {"() {"}
      </>
    ),
  },
  {
    n: 6,
    jsx: (
      <>
        {"  "}
        <span style={{ color: "#8e9cd6" }}>const</span>
        {" { todos, add, toggle, remaining } = "}
        <span style={{ color: "#9fb0d2" }}>useTodos</span>
        {"()"}
      </>
    ),
  },
  {
    n: 7,
    jsx: (
      <>
        {"  "}
        <span style={{ color: "#8e9cd6" }}>return</span>
        {" ("}
      </>
    ),
  },
  {
    n: 8,
    jsx: (
      <>
        {"    <"}
        <span style={{ color: "#cf9a93" }}>main</span>
        {" "}
        <span style={{ color: "#9fb0d2" }}>className</span>
        {"="}
        <span style={{ color: "#8fb89a" }}>"app"</span>
        {">"}
      </>
    ),
  },
  {
    n: 9,
    jsx: (
      <>
        {"      <"}
        <span style={{ color: "#cf9a93" }}>header</span>
        {">My Tasks <"}
        <span style={{ color: "#cf9a93" }}>small</span>
        {">{remaining} left</"}
        <span style={{ color: "#cf9a93" }}>small</span>
        {"></"}
        <span style={{ color: "#cf9a93" }}>header</span>
        {">"}
      </>
    ),
  },
  {
    n: 10,
    jsx: (
      <>
        {"      <"}
        <span style={{ color: "#cf9a93" }}>TodoList</span>
        {" "}
        <span style={{ color: "#9fb0d2" }}>items</span>
        {"={todos} "}
        <span style={{ color: "#9fb0d2" }}>onToggle</span>
        {"={toggle} />"}
      </>
    ),
  },
  {
    n: 11,
    jsx: (
      <>
        {"      <"}
        <span style={{ color: "#cf9a93" }}>AddTodo</span>
        {" "}
        <span style={{ color: "#9fb0d2" }}>onAdd</span>
        {"={add} />"}
      </>
    ),
  },
  {
    n: 12,
    jsx: (
      <>
        {"    </"}
        <span style={{ color: "#cf9a93" }}>main</span>
        {">"}
      </>
    ),
  },
  { n: 13, jsx: <>{"  )"}</> },
  { n: 14, jsx: <>{"}"}</> },
];

const BUILD_STEPS = [
  { status: "done" as const, title: "Scaffold Vite + React + TS", meta: "7 files - 1.4s" },
  { status: "done" as const, title: "Write TodoList + AddTodo", meta: "components/ - 2 files" },
  { status: "running" as const, title: "Add useTodos hook", meta: "wiring localStorage persistence..." },
  { status: "queued" as const, title: "Install dependencies", meta: "npm i - queued" },
  { status: "queued" as const, title: "Start dev server + preview", meta: "queued" },
];

function StepIcon({ status }: { status: "done" | "running" | "queued" }) {
  if (status === "done") {
    return (
      <div className="flex h-5 w-5 flex-none items-center justify-center rounded-full bg-green-500/15 text-green-400">
        <Check size={12} strokeWidth={3} />
      </div>
    );
  }
  if (status === "running") {
    return (
      <div className="flex h-5 w-5 flex-none items-center justify-center rounded-full bg-amber-500/15 text-amber-400">
        <div className="h-3 w-3 animate-spin rounded-full border-2 border-amber-400 border-r-transparent" />
      </div>
    );
  }
  return (
    <div className="flex h-5 w-5 flex-none items-center justify-center rounded-full bg-shell-surface-active text-shell-text-tertiary">
      <Circle size={12} />
    </div>
  );
}

export function BuildView() {
  return (
    <>
      <style>{`@keyframes blink{50%{opacity:0}}`}</style>

      {/* view header */}
      <div
        className="flex flex-none items-center gap-3 border-b border-shell-border px-[22px]"
        style={{ height: "54px" }}
      >
        <h2 className="text-[17px] font-bold tracking-[-0.02em]">Build</h2>
        <span className="text-[12px] text-shell-text-tertiary">
          todo-app - Node + React - runs on fedora-gpu
        </span>
        <div className="ml-auto flex rounded-full border border-shell-border bg-shell-surface p-[3px]">
          <span className="cursor-pointer rounded-full bg-shell-surface-active px-[13px] py-[5px] text-[11px] font-semibold text-shell-text">
            Chat
          </span>
          <span className="cursor-pointer px-[13px] py-[5px] text-[11px] font-semibold text-shell-text-secondary">
            Diff
          </span>
        </div>
      </div>

      {/* three-column body */}
      <div className="flex min-h-0 flex-1">
        {/* column 1: file tree */}
        <div className="w-[190px] flex-none overflow-auto border-r border-shell-border bg-shell-bg-deep px-2 py-2.5">
          <div className="px-2 pb-2 pt-1 text-[10.5px] font-bold uppercase tracking-[0.06em] text-shell-text-tertiary">
            todo-app
          </div>

          {/* src folder */}
          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-[5px] text-[12.5px] text-shell-text-secondary hover:bg-shell-surface">
            <Folder size={13} className="flex-none text-shell-text-tertiary" />
            src
          </div>

          {/* App.tsx - active */}
          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg bg-shell-surface-active px-2 py-[5px] pl-5 text-[12.5px] text-shell-text hover:bg-shell-surface-active">
            <FileText size={13} className="flex-none text-shell-text-tertiary" />
            App.tsx
            <div className="ml-auto h-1.5 w-1.5 flex-none rounded-full bg-amber-400" />
          </div>

          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-[5px] pl-5 text-[12.5px] text-shell-text-secondary hover:bg-shell-surface">
            <FileText size={13} className="flex-none text-shell-text-tertiary" />
            TodoList.tsx
          </div>

          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-[5px] pl-5 text-[12.5px] text-shell-text-secondary hover:bg-shell-surface">
            <FileText size={13} className="flex-none text-shell-text-tertiary" />
            useTodos.ts
          </div>

          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-[5px] pl-5 text-[12.5px] text-shell-text-secondary hover:bg-shell-surface">
            <FileText size={13} className="flex-none text-shell-text-tertiary" />
            styles.css
          </div>

          {/* root files */}
          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-[5px] text-[12.5px] text-shell-text-secondary hover:bg-shell-surface">
            <FileText size={13} className="flex-none text-shell-text-tertiary" />
            index.html
          </div>

          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-[5px] text-[12.5px] text-shell-text-secondary hover:bg-shell-surface">
            <FileText size={13} className="flex-none text-shell-text-tertiary" />
            package.json
          </div>

          <div className="flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-[5px] text-[12.5px] text-shell-text-secondary hover:bg-shell-surface">
            <FileText size={13} className="flex-none text-shell-text-tertiary" />
            vite.config.ts
          </div>
        </div>

        {/* column 2: editor */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* tabs bar */}
          <div className="flex h-[38px] flex-none items-stretch border-b border-shell-border bg-shell-bg-deep">
            <div className="flex cursor-pointer items-center gap-2 border-r border-shell-border bg-shell-bg px-4 text-[12px] text-shell-text shadow-[inset_0_-2px_0_0_var(--color-accent,#8b92a3)]">
              App.tsx
              <span className="text-[13px] opacity-50">x</span>
            </div>
            <div className="flex cursor-pointer items-center gap-2 bg-transparent px-4 text-[12px] text-shell-text-tertiary">
              useTodos.ts
              <span className="text-[13px] opacity-50">x</span>
            </div>
          </div>

          {/* code area */}
          <div className="flex-1 overflow-auto py-3.5 font-mono text-[12.5px] leading-[1.62]">
            {CODE_LINES.map(({ n, jsx }) => (
              <div
                key={n}
                className={`flex px-0${n === 10 ? " bg-shell-surface" : ""}`}
              >
                <span className="w-[46px] flex-none select-none pr-4 text-right text-shell-text-tertiary opacity-60">
                  {n}
                </span>
                <span className="whitespace-pre text-shell-text">
                  {jsx}
                  {n === 10 && (
                    <span
                      aria-hidden
                      className="inline-block w-[2px] h-[15px] bg-accent align-[-3px]"
                      style={{ animation: "blink 1s steps(1) infinite" }}
                    />
                  )}
                </span>
              </div>
            ))}
          </div>

          {/* terminal strip */}
          <div className="h-[96px] flex-none overflow-auto border-t border-shell-border bg-shell-bg-deep px-4 py-2.5 font-mono">
            <div className="text-[11.5px] leading-[1.7]">
              <span className="text-accent">~/todo-app</span>
              {" $ npm run dev"}
            </div>
            <div className="text-[11.5px] leading-[1.7]">
              <span className="text-green-400">VITE v5.4</span>
              {" ready in 412 ms"}
            </div>
            <div className="text-[11.5px] leading-[1.7]">
              {"> Local: "}
              <span className="text-blue-400">http://todo-app.taos.local</span>
              {" "}
              <span className="text-green-400">live</span>
            </div>
          </div>
        </div>

        {/* column 3: build log */}
        <div className="flex w-[296px] flex-none flex-col border-l border-shell-border">
          {/* header */}
          <div className="flex items-center gap-2 px-[18px] pb-2.5 pt-4 text-[13px] font-bold tracking-[-0.01em]">
            <ClipboardCheck size={16} className="text-accent" />
            Build log
          </div>

          {/* steps */}
          <div className="flex flex-1 flex-col gap-0.5 overflow-auto px-3.5 pb-3.5 pt-0.5">
            {BUILD_STEPS.map((step) => (
              <div
                key={step.title}
                className="flex gap-[11px] rounded-[11px] px-2.5 py-[9px] hover:bg-shell-surface"
              >
                <StepIcon status={step.status} />
                <div>
                  <div className="text-[12.5px] font-semibold text-shell-text">{step.title}</div>
                  <div className="mt-0.5 text-[11px] leading-[1.4] text-shell-text-tertiary">
                    {step.meta}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* footer */}
          <div className="flex flex-none flex-col gap-3 border-t border-shell-border p-3.5">
            {/* model pill */}
            <div className="flex cursor-pointer items-center gap-2.5 rounded-[13px] border border-shell-border bg-shell-surface px-3 py-2.5">
              <div
                className="h-[26px] w-[26px] flex-none rounded-[8px]"
                style={{ background: "linear-gradient(135deg,#7c8ba1,#aab4c9)" }}
              />
              <div>
                <div className="text-[12.5px] font-semibold">Qwen2.5-Coder 7B</div>
                <div className="text-[10.5px] text-shell-text-tertiary">local - fedora-gpu</div>
              </div>
              <ChevronDown size={14} className="ml-auto text-shell-text-tertiary" />
            </div>

            {/* open preview button */}
            <div className="flex h-[42px] cursor-pointer items-center justify-center gap-2 rounded-[13px] border border-shell-border bg-shell-surface text-[12.5px] font-semibold hover:bg-shell-surface-active">
              <Play size={15} />
              Open live preview
            </div>
          </div>
        </div>
      </div>

      {/* prompt bar */}
      <div className="flex flex-none items-end gap-3 border-t border-shell-border bg-shell-bg-deep px-[22px] py-4">
        <textarea
          rows={1}
          placeholder="Describe a feature or paste an error..."
          className="min-h-[50px] flex-1 resize-none rounded-[15px] border border-shell-border bg-shell-surface px-4 py-3.5 text-[13.5px] text-shell-text-tertiary placeholder:text-shell-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent/40"
        />
        <button
          type="button"
          className="flex h-[50px] flex-none cursor-pointer items-center gap-2 rounded-[15px] border-0 px-6 text-[14px] font-bold text-white"
          style={{
            background: "linear-gradient(135deg,#a9b0c2,#8b92a3)",
            boxShadow: "0 8px 22px -8px rgba(139,146,163,0.35)",
          }}
        >
          <Sparkles size={18} />
          Build
        </button>
      </div>
    </>
  );
}
