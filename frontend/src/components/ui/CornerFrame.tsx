import { type ReactNode } from "react";

type SizeKey = "sm" | "md" | "lg";

type Props = {
  children: ReactNode;
  size?: SizeKey;
  className?: string;
};

const triSize: Record<SizeKey, string> = {
  sm: "w-3 h-3 lg:w-3.5 lg:h-3.5",
  md: "w-4 h-4 lg:w-5 lg:h-5",
  lg: "w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7",
};

const triPos: Record<SizeKey, Record<"tl" | "tr" | "bl" | "br", string>> = {
  sm: {
    tl: "-top-3 -left-3 lg:-top-3.5 lg:-left-3.5",
    tr: "-top-3 -right-3 lg:-top-3.5 lg:-right-3.5",
    bl: "-bottom-3 -left-3 lg:-bottom-3.5 lg:-left-3.5",
    br: "-bottom-3 -right-3 lg:-bottom-3.5 lg:-right-3.5",
  },
  md: {
    tl: "-top-4 -left-4 lg:-top-5 lg:-left-5",
    tr: "-top-4 -right-4 lg:-top-5 lg:-right-5",
    bl: "-bottom-4 -left-4 lg:-bottom-5 lg:-left-5",
    br: "-bottom-4 -right-4 lg:-bottom-5 lg:-right-5",
  },
  lg: {
    tl: "-top-5 -left-5 sm:-top-6 sm:-left-6 lg:-top-7 lg:-left-7",
    tr: "-top-5 -right-5 sm:-top-6 sm:-right-6 lg:-top-7 lg:-right-7",
    bl: "-bottom-5 -left-5 sm:-bottom-6 sm:-left-6 lg:-bottom-7 lg:-left-7",
    br: "-bottom-5 -right-5 sm:-bottom-6 sm:-right-6 lg:-bottom-7 lg:-right-7",
  },
};

const dotSize: Record<SizeKey, string> = {
  sm: "w-2 h-2",
  md: "w-3 h-3 lg:w-3.5 lg:h-3.5",
  lg: "w-3.5 h-3.5 sm:w-4 sm:h-4 lg:w-5 lg:h-5",
};

const dotPos: Record<SizeKey, Record<"tl" | "tr" | "bl" | "br", string>> = {
  sm: {
    tl: "-top-1 -left-1",
    tr: "-top-1 -right-1",
    bl: "-bottom-1 -left-1",
    br: "-bottom-1 -right-1",
  },
  md: {
    tl: "-top-1.5 -left-1.5 lg:-top-2 lg:-left-2",
    tr: "-top-1.5 -right-1.5 lg:-top-2 lg:-right-2",
    bl: "-bottom-1.5 -left-1.5 lg:-bottom-2 lg:-left-2",
    br: "-bottom-1.5 -right-1.5 lg:-bottom-2 lg:-right-2",
  },
  lg: {
    tl: "-top-2 -left-2 lg:-top-2.5 lg:-left-2.5",
    tr: "-top-2 -right-2 lg:-top-2.5 lg:-right-2.5",
    bl: "-bottom-2 -left-2 lg:-bottom-2.5 lg:-left-2.5",
    br: "-bottom-2 -right-2 lg:-bottom-2.5 lg:-right-2.5",
  },
};

const BASE = "absolute bg-amber-500 border border-gray-900 pointer-events-none";
const DOT = `${BASE} rounded-full`;

export default function CornerFrame({ children, size = "md", className = "" }: Props) {
  const ts = triSize[size];
  const tp = triPos[size];
  const ds = dotSize[size];
  const dp = dotPos[size];

  return (
    <div className={`relative ${className}`}>
      <span
        aria-hidden="true"
        className={`${BASE} ${ts} ${tp.tl} [clip-path:polygon(100%_100%,100%_0,0_100%)]`}
      />
      <span
        aria-hidden="true"
        className={`${BASE} ${ts} ${tp.tr} [clip-path:polygon(0_100%,0_0,100%_100%)]`}
      />
      <span
        aria-hidden="true"
        className={`${BASE} ${ts} ${tp.bl} [clip-path:polygon(100%_0,0_0,100%_100%)]`}
      />
      <span
        aria-hidden="true"
        className={`${BASE} ${ts} ${tp.br} [clip-path:polygon(0_0,100%_0,0_100%)]`}
      />
      <span aria-hidden="true" className={`${DOT} ${ds} ${dp.tl}`} />
      <span aria-hidden="true" className={`${DOT} ${ds} ${dp.tr}`} />
      <span aria-hidden="true" className={`${DOT} ${ds} ${dp.bl}`} />
      <span aria-hidden="true" className={`${DOT} ${ds} ${dp.br}`} />
      {children}
    </div>
  );
}
