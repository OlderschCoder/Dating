import Link from "next/link";

export function AppHeader() {
  return (
    <header className="border-b border-black/10 dark:border-white/15">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-semibold tracking-tight">
          DatingApp
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/discover" className="hover:underline">
            Discover
          </Link>
          <Link href="/matches" className="hover:underline">
            Matches
          </Link>
          <Link href="/onboarding" className="hover:underline">
            Profile
          </Link>
        </nav>
      </div>
    </header>
  );
}

