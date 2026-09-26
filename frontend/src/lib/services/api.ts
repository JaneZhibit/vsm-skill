/**
 * Универсальный клиент для авторизованных запросов к бэкенду.
 * Автоматически подхватывает токен сессии из localStorage.
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');

  // Извлекаем токен из хранилища (имя ключа берем из authStore)
  try {
    const stored = localStorage.getItem('vsm_conductor_auth_session');
    if (stored) {
      const session = JSON.parse(stored);
      if (session.token) {
        headers.set('Authorization', `Bearer ${session.token}`);
      }
    }
  } catch (e) {
    console.warn('apiFetch: Ошибка чтения сессии из localStorage', e);
  }

  return fetch(url, { ...options, headers });
}
