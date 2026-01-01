import type { Profile } from "@/lib/types";

export function ProfileCard({ profile }: { profile: Profile }) {
  return (
    <div className="w-full rounded-2xl border border-black/10 bg-white p-5 shadow-sm dark:border-white/15 dark:bg-zinc-950">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xl font-semibold">
            {profile.name} <span className="font-normal text-black/60 dark:text-white/60">{profile.age}</span>
          </div>
          <div className="text-sm text-black/60 dark:text-white/60">{profile.city}</div>
        </div>
        <div className="h-12 w-12 rounded-full bg-black/5 dark:bg-white/10" aria-hidden />
      </div>

      <p className="mt-4 text-sm leading-6 text-black/80 dark:text-white/80">{profile.bio}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {profile.interests.map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-black/10 px-3 py-1 text-xs text-black/70 dark:border-white/15 dark:text-white/70"
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}

