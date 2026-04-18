import { Button } from '@/components/ui/button';

interface NavigatorProps {
  isFirst: boolean;
  isLast: boolean;
  onPrev: () => void;
  onNext: () => void;
  onSubmit: () => void;
}

export function Navigator({
  isFirst,
  isLast,
  onPrev,
  onNext,
  onSubmit,
}: NavigatorProps) {
  return (
    <div className="flex items-center justify-between gap-3 pt-4">
      <Button type="button" variant="outline" onClick={onPrev} disabled={isFirst}>
        Previous
      </Button>
      {isLast ? (
        <Button type="button" onClick={onSubmit}>
          Submit
        </Button>
      ) : (
        <Button type="button" onClick={onNext}>
          Next
        </Button>
      )}
    </div>
  );
}
