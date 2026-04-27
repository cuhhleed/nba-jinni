import { QuestionMarkCircleIcon } from "@heroicons/react/24/outline";

type Props = {
  message?: string;
};

export default function EmptyState({ message = "No content to load." }: Props) {
  return (
    <div className="flex items-center gap-2 text-yellow-500">
      <QuestionMarkCircleIcon className="h-5 w-5 shrink-0" />
      <span className="text-sm font-light">{message}</span>
    </div>
  );
}