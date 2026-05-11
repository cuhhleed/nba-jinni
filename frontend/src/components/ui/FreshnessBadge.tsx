type Props = {
  isStale: boolean;
  lastUpdatedAt: string; // ISO datetime string
  size?: "sm" | "md" | "lg";
  className?: string;
};

const sizeClasses = {
  sm: "text-xs px-2 py-0.5",
  md: "text-sm px-3 py-1",
  lg: "text-base px-4 py-1.5",
};

export default function FreshnessBadge({
  isStale,
  lastUpdatedAt,
  size = "md",
  className = "",
}: Props) {
  if (!isStale) {
    return null;
  }

  const formattedTime = new Date(lastUpdatedAt).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <span
      className={`inline-block rounded-full font-medium text-amber-600 bg-amber-50 border border-amber-200 ${sizeClasses[size]} ${className}`}
    >
      As of {formattedTime}
    </span>
  );
}
