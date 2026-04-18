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

/**
 * Stream AI response with TRUE real-time token delivery.
 * 
 * Tokens arrive from the backend in real-time (no artificial queue/delay).
 * A minimal 10ms delay between tokens ensures smooth visual rendering.
 * 
 * Calls onToken(token) for each token received.
 * Calls onDone() when the stream finishes.
 * Calls onError(err) if something fails.
 */
export async function sendMessageStream(message, sessionId, { onToken, onDone, onError }) {
  try {
    const res = await fetch(`${API_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE lines from buffer
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.error) {
              onError(new Error(data.error));
              return;
            }

            if (data.done) {
              onDone();
              return;
            }

            if (data.token) {
              // Deliver token directly — real-time, no queue
              onToken(data.token);
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }

    // Stream ended without explicit done signal
    onDone();
  } catch (err) {
    onError(err);
  }
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
