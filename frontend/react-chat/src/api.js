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
 * Stream AI response token-by-token with adaptive speed.
 * 
 * Speed adapts based on queue size:
 * - Queue < 5:  30ms delay (nice typewriter feel)
 * - Queue 5-15: 15ms delay (faster catch-up)
 * - Queue > 15: 5ms delay + batch 3 tokens (rapid rendering)
 * 
 * Calls onToken(token) for each word/token received.
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

    // Token queue for smooth typewriter effect
    const tokenQueue = [];
    let isProcessing = false;
    let streamDone = false;

    const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    // Adaptive delay based on queue size
    const getDelay = () => {
      const queueSize = tokenQueue.length;
      if (queueSize > 15) return 5;   // Fast catch-up
      if (queueSize > 5) return 15;   // Medium speed
      return 30;                       // Nice typewriter feel
    };

    // How many tokens to process per tick
    const getBatchSize = () => {
      const queueSize = tokenQueue.length;
      if (queueSize > 15) return 3;   // Batch 3 tokens when backed up
      return 1;                        // Normal: 1 at a time
    };

    const processQueue = async () => {
      if (isProcessing) return;
      isProcessing = true;

      while (tokenQueue.length > 0) {
        const batchSize = getBatchSize();
        const currentDelay = getDelay();

        // Process batch
        let batchText = '';
        for (let i = 0; i < batchSize && tokenQueue.length > 0; i++) {
          batchText += tokenQueue.shift();
        }
        if (batchText) {
          onToken(batchText);
        }

        await delay(currentDelay);
      }

      isProcessing = false;

      // If stream finished and queue is empty, call onDone
      if (streamDone && tokenQueue.length === 0) {
        onDone();
      }
    };

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
              streamDone = true;
              // Process remaining tokens then call onDone
              if (tokenQueue.length === 0 && !isProcessing) {
                onDone();
              }
              return;
            }

            if (data.token) {
              tokenQueue.push(data.token);
              processQueue(); // Start processing if not already
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }

    // Ensure remaining tokens are processed
    streamDone = true;
    if (tokenQueue.length > 0) {
      await processQueue();
    } else if (!isProcessing) {
      onDone();
    }
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
