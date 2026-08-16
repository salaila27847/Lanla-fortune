import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { backendFetch } from "@/lib/backend";

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const body = await request.text();
  const res = await backendFetch(
    "/api/oracle/draw",
    { method: "POST", headers: { "Content-Type": "application/json" }, body },
    session,
  );

  const responseBody = await res.text();
  return new NextResponse(responseBody, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
  });
}
