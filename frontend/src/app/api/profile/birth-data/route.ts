import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { backendFetch } from "@/lib/backend";

export async function GET() {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const res = await backendFetch("/api/profile/birth-data", { method: "GET" }, session);

  const responseBody = await res.text();
  return new NextResponse(responseBody, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
  });
}

export async function DELETE() {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const res = await backendFetch("/api/profile/birth-data", { method: "DELETE" }, session);

  return new NextResponse(null, { status: res.status });
}
