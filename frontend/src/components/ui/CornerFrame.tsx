import { type ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
};

export default function CornerFrame({ children, className = "" }: Props) {
  return (
    <div className={`relative ${className}`}>
      <span aria-hidden="true" className="absolute -top-4 -left-4 w-4 h-4 bg-amber-400 [clip-path:polygon(100%_100%,100%_0,0_100%)] pointer-events-none" />
      <span aria-hidden="true" className="absolute -top-4 -right-4 w-4 h-4 bg-amber-400 [clip-path:polygon(0_100%,0_0,100%_100%)] pointer-events-none" />
      <span aria-hidden="true" className="absolute -bottom-4 -left-4 w-4 h-4 bg-amber-400 [clip-path:polygon(100%_0,0_0,100%_100%)] pointer-events-none" />
      <span aria-hidden="true" className="absolute -bottom-4 -right-4 w-4 h-4 bg-amber-400 [clip-path:polygon(0_0,100%_0,0_100%)] pointer-events-none" />
      <span aria-hidden="true" className="absolute -top-1.5 -left-1.5 w-3 h-3 rounded-full bg-amber-400 pointer-events-none" />
      <span aria-hidden="true" className="absolute -top-1.5 -right-1.5 w-3 h-3 rounded-full bg-amber-400 pointer-events-none" />
      <span aria-hidden="true" className="absolute -bottom-1.5 -left-1.5 w-3 h-3 rounded-full bg-amber-400 pointer-events-none" />
      <span aria-hidden="true" className="absolute -bottom-1.5 -right-1.5 w-3 h-3 rounded-full bg-amber-400 pointer-events-none" />
      {children}
    </div>
  );
}