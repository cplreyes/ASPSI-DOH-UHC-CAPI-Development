import { Button } from '@/components/ui/button';
import { useInstallPrompt } from '@/lib/install-prompt';

export default function App() {
  const { canInstall, install } = useInstallPrompt();

  return (
    <main className="flex h-full flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-semibold tracking-tight">Hello F2</h1>
      <p className="text-muted-foreground">
        Healthcare Worker Survey — offline-capable PWA
      </p>
      {canInstall ? (
        <Button onClick={install}>Install F2</Button>
      ) : (
        <p className="text-sm text-muted-foreground">
          Open in Chrome or install via your browser menu (iOS: Share → Add to Home Screen)
        </p>
      )}
    </main>
  );
}
