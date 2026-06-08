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
export function formatTimeRemaining(timeRemaining: TimeRemaining): string {
  if (timeRemaining.isExpired) {
    return 'Истек срок';
  }

  const { days, hours, minutes } = timeRemaining;

  if (days > 0) {
    if (hours > 0) {
      return `${days} ${pluralizeDays(days)} ${hours} ${pluralizeHours(hours)}`;
    }
    return `${days} ${pluralizeDays(days)}`;
  }

  if (hours > 0) {
    if (minutes > 0) {
      return `${hours} ${pluralizeHours(hours)} ${minutes} ${pluralizeMinutes(minutes)}`;
    }
    return `${hours} ${pluralizeHours(hours)}`;
  }

  if (minutes > 0) {
    return `${minutes} ${pluralizeMinutes(minutes)}`;
  }

  return 'Меньше минуты';
}

/**
 * Format expiration date as a readable string
 */
export function formatExpirationDate(expiresAt: string | null): string {
  if (!expiresAt) {
    return 'Без ограничения';
  }

  const date = new Date(expiresAt);
  return new Intl.DateTimeFormat('ru-RU', {
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
export function getExpirationTypeLabel(expirationType: string): string {
  const labels: Record<string, string> = {
    unlimited: 'Без ограничения',
    '7_days': '7 дней',
    '14_days': '14 дней',
    '30_days': '30 дней',
  };

  return labels[expirationType] || expirationType;
}

// Helper functions for Russian pluralization
function pluralizeDays(count: number): string {
  if (count % 10 === 1 && count % 100 !== 11) return 'день';
  if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return 'дня';
  return 'дней';
}

function pluralizeHours(count: number): string {
  if (count % 10 === 1 && count % 100 !== 11) return 'час';
  if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return 'часа';
  return 'часов';
}

function pluralizeMinutes(count: number): string {
  if (count % 10 === 1 && count % 100 !== 11) return 'минута';
  if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return 'минуты';
  return 'минут';
}
