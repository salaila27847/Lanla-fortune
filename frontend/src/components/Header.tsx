import Link from "next/link";
import AuthButton from "@/components/AuthButton";

export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
      <Link
        href="/"
        className="text-sm font-semibold tracking-wide text-zinc-950 dark:text-zinc-50"
      >
        LANLA FORTUNE
      </Link>
      <AuthButton />
    </header>
  );
}
