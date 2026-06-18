/**
 * Time utilities for album expiration
 */

export interface TimeRemaining {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  totalSeconds: number;
  isExpired: boolean;
}

type TranslationFn = (key: string, options?: Record<string, unknown>) => string;

const defaultTranslate: TranslationFn = (key) => {
  const fallbacks: Record<string, string> = {
    'time.expired': 'Expired',
    'time.lessThanMinute': 'Less than a minute',
    'time.unlimited': 'Unlimited',
  };
  return fallbacks[key] || key;
};

/**
 * Calculate time remaining until expiration
 */
export function calculateTimeRemaining(expiresAt: string | null): TimeRemaining {
  if (!expiresAt) {
    return {
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      totalSeconds: 0,
      isExpired: false,
    };
  }

  const now = new Date();
  const expirationDate = new Date(expiresAt);
  const diffMs = expirationDate.getTime() - now.getTime();

  if (diffMs <= 0) {
    return {
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      totalSeconds: 0,
      isExpired: true,
    };
  }

  const totalSeconds = Math.floor(diffMs / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return {
    days,
    hours,
    minutes,
    seconds,
    totalSeconds,
    isExpired: false,
  };
}

/**
 * Format time remaining as a human-readable string
 */
export function formatTimeRemaining(timeRemaining: TimeRemaining, t: TranslationFn = defaultTranslate): string {
  if (timeRemaining.isExpired) {
    return t('time.expired');
  }

  const { days, hours, minutes } = timeRemaining;

  if (days > 0) {
    if (hours > 0) {
      return `${days} ${t('time.days', { count: days })} ${hours} ${t('time.hours', { count: hours })}`;
    }
    return `${days} ${t('time.days', { count: days })}`;
  }

  if (hours > 0) {
    if (minutes > 0) {
      return `${hours} ${t('time.hours', { count: hours })} ${minutes} ${t('time.minutes', { count: minutes })}`;
    }
    return `${hours} ${t('time.hours', { count: hours })}`;
  }

  if (minutes > 0) {
    return `${minutes} ${t('time.minutes', { count: minutes })}`;
  }

  return t('time.lessThanMinute');
}

/**
 * Format expiration date as a readable string
 */
export function formatExpirationDate(expiresAt: string | null, locale = 'en-GB', t: TranslationFn = defaultTranslate): string {
  if (!expiresAt) {
    return t('time.unlimited');
  }

  const date = new Date(expiresAt);
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

/**
 * Get color class based on time remaining
 */
export function getExpirationColor(timeRemaining: TimeRemaining): string {
  if (timeRemaining.isExpired) {
    return 'text-red-600 dark:text-red-400';
  }

  const { days } = timeRemaining;

  if (days > 7) {
    return 'text-green-600 dark:text-green-400';
  }

  if (days >= 2) {
    return 'text-yellow-600 dark:text-yellow-400';
  }

  return 'text-orange-600 dark:text-orange-400';
}

/**
 * Get background color class based on time remaining
 */
export function getExpirationBgColor(timeRemaining: TimeRemaining): string {
  if (timeRemaining.isExpired) {
    return 'bg-red-50 dark:bg-red-900/20';
  }

  const { days } = timeRemaining;

  if (days > 7) {
    return 'bg-green-50 dark:bg-green-900/20';
  }

  if (days >= 2) {
    return 'bg-yellow-50 dark:bg-yellow-900/20';
  }

  return 'bg-orange-50 dark:bg-orange-900/20';
}

/**
 * Get expiration type label
 */
export function getExpirationTypeLabel(expirationType: string, t: TranslationFn = defaultTranslate): string {
  if (expirationType === 'unlimited') return t('time.unlimited');
  return t(`time.${expirationType}`) || expirationType;
}
