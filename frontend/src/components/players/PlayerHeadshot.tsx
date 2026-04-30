import logoPlaceholder from "../../assets/logo-placeholder-2.svg";

type Props = {
  playerId: number;
  alt?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const sizeClasses = {
  sm: "w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10",
  md: "w-12 h-12 sm:w-16 sm:h-16 lg:w-24 lg:h-24",
  lg: "w-32 h-32 sm:w-40 sm:h-40 lg:w-64 lg:h-64",
};

export default function PlayerHeadshot({
  playerId,
  alt = "Player headshot",
  size = "md",
  className = "",
}: Props) {
  return (
    <img
      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${playerId}.png`}
      alt={alt}
      className={`${sizeClasses[size]} object-contain ${className}`}
      onError={(e) => {
        e.currentTarget.src = logoPlaceholder;
        e.currentTarget.onerror = null;
      }}
    />
  );
}
