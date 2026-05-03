import { type ReactNode } from "react";
import CornerFrame from "./CornerFrame";

type SizeKey = "sm" | "md" | "lg";

type Props = {
  children: ReactNode;
  size?: SizeKey;
  className?: string;
  hoverable?: boolean;
};

export default function CarpetBadge({ children, size = "md", className = "", hoverable = false }: Props) {
  return (
    <CornerFrame
      size={size}
      className={`bg-gray-900 border-4 border-amber-500 border-double${hoverable ? " hover:shadow-lg hover:scale-105 transition-all" : ""} ${className}`}
    >
      {children}
    </CornerFrame>
  );
}
