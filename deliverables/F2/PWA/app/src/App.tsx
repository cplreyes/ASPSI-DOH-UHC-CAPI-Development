import { Button } from '@/components/ui/button';
import { Section } from '@/components/survey/Section';
import { sectionA } from '@/generated/items';
import { sectionASchema, type SectionAValues } from '@/generated/schema';
import { useInstallPrompt } from '@/lib/install-prompt';

export default function App() {
  const { canInstall, install } = useInstallPrompt();

  const handleSubmit = (values: SectionAValues) => {
    // M2 replaces this with an IndexedDB write.
    // eslint-disable-next-line no-console
    console.log('Section A submitted:', values);
    alert(`Submitted:\n${JSON.stringify(values, null, 2)}`);
  };

  return (
    <main className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-lg font-semibold">F2 Survey</h1>
        {canInstall ? (
          <Button size="sm" onClick={install}>
            Install
          </Button>
        ) : null}
      </header>
      <Section section={sectionA} schema={sectionASchema} onSubmit={handleSubmit} />
    </main>
  );
}
