import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "@/auth";
import { backendFetch } from "@/lib/backend";
import type { ReadingRecord } from "@/lib/api";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("th-TH", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default async function HistoryPage() {
  const session = await auth();
  if (!session?.user) {
    redirect("/");
  }

  const res = await backendFetch("/api/readings", { method: "GET" }, session);
  if (!res.ok) {
    throw new Error(`Failed to load reading history: ${res.status}`);
  }
  const readings: ReadingRecord[] = await res.json();

  return (
    <div className="flex flex-1 flex-col bg-zinc-50 px-6 py-16 dark:bg-black">
      <div className="mx-auto w-full max-w-2xl">
        <h1 className="mb-8 text-2xl font-semibold text-zinc-950 dark:text-zinc-50">
          ประวัติคำทำนายของคุณ
        </h1>

        {readings.length === 0 ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            ยังไม่มีประวัติคำทำนาย ลอง{" "}
            <Link href="/reading" className="underline">
              ดูดวง
            </Link>{" "}
            ดูสิ
          </p>
        ) : (
          <ul className="flex flex-col gap-4">
            {readings.map((reading) => (
              <li
                key={reading.id}
                className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-sm font-medium text-zinc-950 dark:text-zinc-50">
                    {reading.birth_data?.place ??
                      (reading.synthesis.oracle_question
                        ? `คำถาม: ${reading.synthesis.oracle_question}`
                        : "ไม่ใช้ข้อมูลวันเกิด")}
                  </span>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {formatDate(reading.created_at)}
                  </span>
                </div>
                <details>
                  <summary className="cursor-pointer text-sm text-zinc-600 dark:text-zinc-400">
                    ดูคำทำนายฉบับสมบูรณ์
                  </summary>
                  <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-700 dark:text-zinc-300">
                    {reading.synthesis.final_reading}
                  </p>
                </details>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
