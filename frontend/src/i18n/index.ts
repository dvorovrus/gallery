import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import ru from './locales/ru.json';
import uk from './locales/uk.json';

export type AppLanguage = 'uk' | 'ru' | 'en';

export const LANGUAGE_STORAGE_KEY = 'gallery_language';
export const LANGUAGE_MANUAL_KEY = 'gallery_language_manual';

export const supportedLanguages: AppLanguage[] = ['uk', 'ru', 'en'];

export const languageLabels: Record<AppLanguage, string> = {
  uk: 'Українська',
  ru: 'Русский',
  en: 'English',
};

const normalizeLanguage = (value: string | null | undefined): AppLanguage | null => {
  if (!value) return null;
  const normalized = value.toLowerCase();
  if (normalized.startsWith('uk') || normalized === 'ua') return 'uk';
  if (normalized.startsWith('ru')) return 'ru';
  if (normalized.startsWith('en')) return 'en';
  return null;
};

const languageFromCountry = (country: string | null | undefined): AppLanguage | null => {
  const code = country?.trim().toUpperCase();
  if (code === 'UA') return 'uk';
  if (code === 'RU') return 'ru';
  return code ? 'en' : null;
};

export const getInitialLanguage = (): AppLanguage => {
  const savedLanguage = normalizeLanguage(localStorage.getItem(LANGUAGE_STORAGE_KEY));
  if (localStorage.getItem(LANGUAGE_MANUAL_KEY) === '1' && savedLanguage) {
    return savedLanguage;
  }

  const countryLanguage = languageFromCountry(
    document.documentElement.dataset.country ||
    document.querySelector<HTMLMetaElement>('meta[name="x-country"]')?.content,
  );

  if (countryLanguage) return countryLanguage;

  const browserLanguage = normalizeLanguage(navigator.language || navigator.languages?.[0]);
  return browserLanguage || 'en';
};

i18n
  .use(initReactI18next)
  .init({
    resources: {
      uk: { translation: uk },
      ru: { translation: ru },
      en: { translation: en },
    },
    lng: getInitialLanguage(),
    fallbackLng: 'en',
    supportedLngs: supportedLanguages,
    interpolation: {
      escapeValue: false,
    },
    returnNull: false,
  });

i18n.on('languageChanged', (language) => {
  const normalized = normalizeLanguage(language) || 'en';
  document.documentElement.lang = normalized;
  localStorage.setItem(LANGUAGE_STORAGE_KEY, normalized);
});

document.documentElement.lang = i18n.resolvedLanguage || i18n.language || 'en';

export const setAppLanguage = (language: AppLanguage) => {
  localStorage.setItem(LANGUAGE_MANUAL_KEY, '1');
  void i18n.changeLanguage(language);
};

export const getLocaleForLanguage = (language: string | undefined) => {
  if (language?.startsWith('uk')) return 'uk-UA';
  if (language?.startsWith('ru')) return 'ru-RU';
  return 'en-GB';
};

export default i18n;
