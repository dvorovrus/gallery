import { useTranslation } from 'react-i18next';
import { languageLabels, setAppLanguage, supportedLanguages, type AppLanguage } from '@/i18n';

interface LanguageSwitcherProps {
  compact?: boolean;
}

export default function LanguageSwitcher({ compact = false }: LanguageSwitcherProps) {
  const { i18n, t } = useTranslation();
  const currentLanguage = (i18n.resolvedLanguage || i18n.language || 'en').slice(0, 2) as AppLanguage;

  return (
    <label className="inline-flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400">
      {!compact && <span className="hidden sm:inline">{t('app.language')}</span>}
      <select
        value={currentLanguage}
        onChange={(event) => setAppLanguage(event.target.value as AppLanguage)}
        className="h-10 rounded-full border border-neutral-200 bg-white px-3 text-sm font-medium text-neutral-900 outline-none transition-colors hover:border-neutral-400 dark:border-neutral-800 dark:bg-neutral-900 dark:text-white dark:hover:border-neutral-600"
        aria-label={t('app.language')}
      >
        {supportedLanguages.map((language) => (
          <option key={language} value={language}>
            {compact ? language.toUpperCase() : languageLabels[language]}
          </option>
        ))}
      </select>
    </label>
  );
}
