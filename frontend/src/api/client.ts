import { clearTokens, getTokens, setTokens } from "../auth/tokenStore";

const API_BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  detail?: string;
  constructor(status: number, detail?: string) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  form?: URLSearchParams;
  auth?: boolean;
  _retried?: boolean;
};

async function parseError(res: Response): Promise<string | undefined> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg)
      return data.detail[0].msg;
    return undefined;
  } catch {
    return undefined;
  }
}

export async function api<T = unknown>(
  path: string,
  opts: RequestOptions = {}
): Promise<T> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;

  if (opts.form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    body = opts.form;
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }

  if (opts.auth) {
    const tokens = getTokens();
    if (tokens?.access_token)
      headers["Authorization"] = `Bearer ${tokens.access_token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: opts.method || (body ? "POST" : "GET"),
      headers,
      body,
    });
  } catch {
    throw new ApiError(0, "network");
  }

  if (res.status === 401 && opts.auth && !opts._retried) {
    const refreshed = await tryRefresh();
    if (refreshed) return api<T>(path, { ...opts, _retried: true });
    clearTokens();
    throw new ApiError(401, await parseError(res));
  }

  if (!res.ok) {
    throw new ApiError(res.status, await parseError(res));
  }

  if (res.status === 204) return undefined as unknown as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;
  const tokens = getTokens();
  if (!tokens?.refresh_token) return false;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: tokens.refresh_token }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      setTokens(data);
      return true;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}