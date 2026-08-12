import Link from "next/link";
import { headers } from "next/headers";
import { auth, signIn, signOut } from "@/auth";

export default async function AuthButton() {
  const session = await auth();

  if (!session?.user) {
    return (
      <form
        action={async () => {
          "use server";
          const referer = (await headers()).get("referer");
          const callbackUrl = referer ? new URL(referer).searchParams.get("callbackUrl") : null;
          await signIn("google", callbackUrl ? { redirectTo: callbackUrl } : undefined);
        }}
      >
        <button
          type="submit"
          className="rounded-full border border-zinc-300 px-4 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          เข้าสู่ระบบด้วย Google
        </button>
      </form>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-zinc-700 dark:text-zinc-300">
        {session.user.name ?? session.user.email}
      </span>
      <Link
        href="/history"
        className="text-sm text-zinc-700 underline-offset-2 hover:underline dark:text-zinc-300"
      >
        ดูประวัติคำทำนาย
      </Link>
      <form
        action={async () => {
          "use server";
          await signOut();
        }}
      >
        <button
          type="submit"
          className="rounded-full border border-zinc-300 px-4 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          ออกจากระบบ
        </button>
      </form>
    </div>
  );
}
