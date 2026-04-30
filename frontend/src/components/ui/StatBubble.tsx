type Props = {
  value: string | number | undefined;
  label?: string;
  sublabel?: string;
  size?: "md" | "lg";
  bubble?: boolean;
  valueColor?: string;
  labelColor?: string;

  className?: string;
};

const bubbleClasses = {
  md: "w-11 h-11 sm:w-14 sm:h-14 lg:w-18 lg:h-18 text-base sm:text-lg lg:text-xl",
  lg: "w-14 h-14  sm:w-16 sm:h-16 lg:w-20 lg:h-20 text-xl sm:text-2xl lg:text-3xl",
};

export default function StatBubble({
  value,
  label,
  sublabel,
  size = "md",
  bubble = true,
  valueColor = "text-sky-600 group-hover:text-amber-500",
  labelColor = "text-gray-900",
  className = "",
}: Props) {
  return (
    <div className={`flex flex-col items-center m-4 ${className}`}>
      {label && (
        <span
          className={`text-xs sm:text-sm lg:text-base ${labelColor} font-medium text-center`}
        >
          {label}
        </span>
      )}
      <div
        className={`${bubble ? "border rounded-xl bg-white" : ""} ${valueColor} font-brand flex items-center justify-center ${bubbleClasses[size]}`}
      >
        {value}
      </div>
      {sublabel && (
        <span className={`text-xs sm:text-xs lg:text-sm ${labelColor} text-center`}>
          {sublabel}
        </span>
      )}
    </div>
  );
}
