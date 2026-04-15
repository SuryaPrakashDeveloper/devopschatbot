const API_URL = 'http://localhost:8000';

export async function checkApiStatus() {
  try {
    const res = await fetch(`${API_URL}/`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function sendMessage(message, sessionId) {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal: AbortSignal.timeout(120000),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function clearSession(sessionId) {
  try {
    await fetch(`${API_URL}/session/${sessionId}/clear`, {
      method: 'POST',
      signal: AbortSignal.timeout(5000),
    });
  } catch {
    // Silently fail
  }
}
