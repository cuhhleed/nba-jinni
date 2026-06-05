import mainLogo from "../../../public/NBAJINNI.png";

type Props = {
  className?: string;
};

export default function MainLogo({ className = "" }: Props) {
  return (
    <img
      src={mainLogo}
      alt="NBA Jinni"
      className={`h-7 w-auto sm:h-8 lg:h-9 ${className}`}
    />
  );
}
