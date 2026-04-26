interface Props {
  message: string;
}

export function BroadcastBanner({ message }: Props) {
  if (!message) return null;
  return (
    <div role="status" className="border-b bg-warning/10 px-6 py-2 text-sm text-warning">
      {message}
    </div>
  );
}
