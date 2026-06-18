import { useEffect } from 'react';
import { LANGUAGE_MANUAL_KEY, LANGUAGE_STORAGE_KEY, setAppLanguage, type AppLanguage } from '@/i18n';

const countryToLanguage = (country: string | null): AppLanguage | null => {
  if (country === 'UA') return 'uk';
  if (country === 'RU') return 'ru';
  if (country) return 'en';
  return null;
};

export default function GeoLanguage() {
  useEffect(() => {
    if (localStorage.getItem(LANGUAGE_MANUAL_KEY) === '1') return;

    const controller = new AbortController();

    fetch('/api/geo', { signal: controller.signal })
      .then((response) => response.ok ? response.json() : null)
      .then((data) => {
        const language = countryToLanguage(data?.country || null);
        if (!language || localStorage.getItem(LANGUAGE_STORAGE_KEY) === language) return;
        setAppLanguage(language);
        localStorage.removeItem(LANGUAGE_MANUAL_KEY);
      })
      .catch(() => {});

    return () => controller.abort();
  }, []);

  return null;
}
