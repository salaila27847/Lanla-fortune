import type { Session } from "next-auth";

// Server-only — only ever import this from Route Handlers or Server
// Components, never from a "use client" file. It carries INTERNAL_API_SECRET.
export async function backendFetch(
  path: string,
  init: RequestInit,
  session: Session,
): Promise<Response> {
  const baseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
  const internalSecret = process.env.INTERNAL_API_SECRET;
  if (!internalSecret) {
    throw new Error("INTERNAL_API_SECRET is not set");
  }
  if (!session.user?.id || !session.user.email) {
    throw new Error("backendFetch called without an authenticated user");
  }

  const headers = new Headers(init.headers);
  headers.set("X-Internal-Secret", internalSecret);
  headers.set("X-User-Id", session.user.id);
  headers.set("X-User-Email", session.user.email);
  if (session.user.name) headers.set("X-User-Name", session.user.name);

  return fetch(`${baseUrl}${path}`, { ...init, headers, cache: "no-store" });
}
