import { ExclamationCircleIcon } from "@heroicons/react/24/outline";

type Props = {
  message?: string;
};

export default function ErrorState({ message = "Something went wrong." }: Props) {
  return (
    <div className="flex items-center gap-2 text-red-500">
      <ExclamationCircleIcon className="h-5 w-5 shrink-0" />
      <span className="text-sm">{message}</span>
    </div>
  );
}
