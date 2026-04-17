import { Button } from '@/components/ui/button';

export default function App() {
  return (
    <main className="flex h-full flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-semibold tracking-tight">Hello F2</h1>
      <p className="text-muted-foreground">
        Healthcare Worker Survey — offline-capable PWA
      </p>
      <Button>Install (coming in M0.10)</Button>
    </main>
  );
}
