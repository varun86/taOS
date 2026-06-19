/**
 * Client for the taOS account / identity service (taOSgo P1).
 *
 * Calls are same-origin against the host at /api/account/*, which the controller
 * proxies to taos.my. Same-origin keeps the taos.my base URL server-side and
 * avoids CORS, and lets the host attach host-linking context later.
 *
 * The backend proxy may not exist yet; every call degrades to a clear state
 * (signed-out / unavailable) rather than throwing, so the UI ships ahead of it.
 */

export type TaosgoStatus = "none" | "trialing" | "active" | "past_due";

export interface TaosgoEntitlement {
  status: TaosgoStatus;
  trial_ends_at?: string | null;
  current_period_end?: string | null;
}

export interface Account {
  user_id: string;
  email: string;
  taosgo: TaosgoEntitlement;
}

export type AccountState =
  | { kind: "loading" }
  | { kind: "signed-out" }
  | { kind: "signed-in"; account: Account }
  | { kind: "unavailable" };

export interface AuthError {
  message: string;
}

const BASE = "/api/account";

async function call(path: string, body?: unknown): Promise<Response> {
  return fetch(`${BASE}${path}`, {
    method: body !== undefined ? "POST" : "GET",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: "include",
  });
}

export async function fetchAccount(): Promise<AccountState> {
  let r: Response;
  try {
    r = await call("/me");
  } catch {
    return { kind: "unavailable" };
  }
  if (r.status === 401) return { kind: "signed-out" };
  if (!r.ok) return { kind: "unavailable" };
  try {
    return { kind: "signed-in", account: (await r.json()) as Account };
  } catch {
    return { kind: "unavailable" };
  }
}

async function authAction(
  path: string,
  email: string,
  password: string,
): Promise<Account | AuthError> {
  let r: Response;
  try {
    r = await call(path, { email, password });
  } catch {
    return { message: "Could not reach the account service. Check your connection." };
  }
  if (r.status === 404 || r.status === 503) {
    return { message: "The account service is not available yet." };
  }
  if (!r.ok) {
    let msg = `Request failed (${r.status}).`;
    try {
      const d = (await r.json()) as { error?: string; detail?: string };
      if (d?.error || d?.detail) msg = String(d.error || d.detail);
    } catch {
      /* keep the status-code default */
    }
    return { message: msg };
  }
  try {
    return (await r.json()) as Account;
  } catch {
    return { message: "Unexpected response from the account service." };
  }
}

export const login = (email: string, password: string) =>
  authAction("/login", email, password);

export const register = (email: string, password: string) =>
  authAction("/register", email, password);

export async function logout(): Promise<void> {
  try {
    await call("/logout", {});
  } catch {
    /* signing out client-side is enough even if the call fails */
  }
}

export function isAuthError(x: Account | AuthError): x is AuthError {
  return (x as AuthError).message !== undefined;
}
