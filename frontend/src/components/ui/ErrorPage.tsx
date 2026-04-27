import ErrorState from "./ErrorState";

type Props = {
  message?: string;
};

export default function ErrorPage({ message }: Props) {
  return (
    <div className="flex items-center justify-center p-8">
      <ErrorState message={message} />
    </div>
  );
}
