"use client";

export function SwipeButtons({
  onPass,
  onLike,
}: {
  onPass: () => void;
  onLike: () => void;
}) {
  return (
    <div className="mt-4 grid w-full grid-cols-2 gap-3">
      <button
        type="button"
        onClick={onPass}
        className="h-11 rounded-xl border border-black/10 bg-white text-sm font-medium hover:bg-black/[0.03] dark:border-white/15 dark:bg-zinc-950 dark:hover:bg-white/[0.06]"
      >
        Pass
      </button>
      <button
        type="button"
        onClick={onLike}
        className="h-11 rounded-xl bg-black text-sm font-medium text-white hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80"
      >
        Like
      </button>
    </div>
  );
}

