import Link from "next/link";

export function Logo({ size = "md" }: { size?: "sm" | "md" }) {
  const iconSize = size === "sm" ? "size-8" : "size-8";
  const textSize = size === "sm" ? "text-xl" : "text-xl";

  return (
    <Link href="/" className="flex items-center gap-2">
      <div
        className={`${iconSize} flex items-center justify-center rounded-lg bg-brand`}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M10 2L3 6v8l7 4 7-4V6l-7-4zM10 10l7-4M10 10v8M10 10L3 6"
            stroke="white"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <span
        className={`${textSize} font-bold tracking-tight text-slate-900`}
      >
        Botlixio
      </span>
    </Link>
  );
}
