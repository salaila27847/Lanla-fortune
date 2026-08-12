import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 px-6 py-24 text-center dark:bg-black">
      <p className="mb-3 text-sm font-medium tracking-wide text-zinc-500 dark:text-zinc-400">
        LANLA FORTUNE
      </p>
      <h1 className="max-w-xl text-3xl font-semibold leading-tight text-zinc-950 sm:text-4xl dark:text-zinc-50">
        ดูดวงผสาน 3 ศาสตร์ในคำทำนายเดียว
      </h1>
      <p className="mt-4 max-w-md text-base leading-7 text-zinc-600 dark:text-zinc-400">
        โหราศาสตร์ยูเรเนียน ไพ่ทาโรต์ และไพ่ออราเคิล วิเคราะห์คู่ขนานแล้วสังเคราะห์
        เป็นคำทำนายฉบับสมบูรณ์เดียว
      </p>
      <Link
        href="/reading"
        className="mt-10 rounded-full bg-zinc-950 px-8 py-3 text-sm font-medium text-zinc-50 transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-950 dark:hover:bg-zinc-200"
      >
        เริ่มดูดวง
      </Link>
    </div>
  );
}
