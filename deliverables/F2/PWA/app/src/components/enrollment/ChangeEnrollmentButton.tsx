import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { DRAFT_ID_KEY } from '@/lib/draft';

export function ChangeEnrollmentButton() {
  const { t } = useTranslation();
  const { unenroll } = useAuth();

  const handleClick = async () => {
    const hasDraft = !!localStorage.getItem(DRAFT_ID_KEY);
    const msg = hasDraft ? t('enrollment.changeConfirmWithDraft') : t('enrollment.changeConfirm');
    if (!window.confirm(msg)) return;
    await unenroll();
  };

  return (
    <Button variant="outline" size="sm" onClick={handleClick}>
      {t('enrollment.changeButton')}
    </Button>
  );
}
