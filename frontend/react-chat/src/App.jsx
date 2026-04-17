import { useState, useEffect, useRef, useCallback } from 'react';
import MatrixRain from './MatrixRain';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import ChatInput from './ChatInput';
import { checkApiStatus, sendMessageStream, clearSession } from './api';

function generateId() {
  return crypto.randomUUID?.() || Math.random().toString(36).slice(2);
}

// Quick action buttons for DevOps queries
const QUICK_ACTIONS = [
  { label: '☸️ K8s Basics', query: 'What are the key Kubernetes concepts I should know?' },
  { label: '🐳 Docker Help', query: 'Show me essential Docker commands for managing containers' },
  { label: '📋 Check Logs', query: 'How do I check pod logs in Kubernetes? Show me kubectl commands' },
  { label: '🔍 Troubleshoot', query: 'What are common Kubernetes pod failure reasons and how to debug them?' },
];

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [sessionId] = useState(() => generateId());
  const messagesEndRef = useRef(null);

  // Check API status
  useEffect(() => {
    const check = async () => setIsOnline(await checkApiStatus());
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = { role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    // Add an empty AI message that we'll fill token-by-token
    const aiMsgIndex = messages.length + 1; // +1 because we just added user msg
    setMessages(prev => [...prev, { role: 'ai', content: '', timestamp: new Date(), streaming: true }]);

    await sendMessageStream(text, sessionId, {
      onToken: (token) => {
        // Append each token to the AI message
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'ai') {
            updated[updated.length - 1] = {
              ...lastMsg,
              content: lastMsg.content + token,
            };
          }
          return updated;
        });
      },
      onDone: () => {
        // Mark streaming as complete
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'ai') {
            updated[updated.length - 1] = { ...lastMsg, streaming: false };
          }
          return updated;
        });
        setIsLoading(false);
      },
      onError: (err) => {
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'ai' && lastMsg.content === '') {
            // Replace empty AI msg with error
            updated[updated.length - 1] = {
              role: 'ai',
              content: `⚠️ Error: ${err.message}`,
              timestamp: new Date(),
              streaming: false,
            };
          } else {
            updated.push({
              role: 'ai',
              content: `⚠️ Error: ${err.message}`,
              timestamp: new Date(),
              streaming: false,
            });
          }
          return updated;
        });
        setIsLoading(false);
      },
    });
  }, [isLoading, sessionId, messages.length]);

  const handleClear = useCallback(async () => {
    await clearSession(sessionId);
    setMessages([]);
  }, [sessionId]);

  return (
    <>
      {/* Matrix Rain Background */}
      <MatrixRain />

      {/* Hero Landing Section */}
      <div className="hero-section">
        <div className="hero-content">
          <div className="hero-icon">☸️</div>
          <h1 className="hero-title">
            DevOps <span className="hero-highlight">AI Assistant</span>
          </h1>
          <p className="hero-subtitle">
            Kubernetes • Docker • CI/CD • Infrastructure • Log Analysis
          </p>
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">☸️</span>
              <span className="hero-stat-label">Kubernetes</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">🐳</span>
              <span className="hero-stat-label">Docker</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">📊</span>
              <span className="hero-stat-label">Monitoring</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">🔧</span>
              <span className="hero-stat-label">CI/CD</span>
            </div>
          </div>
          <p className="hero-cta">
            Click the button below to start chatting →
          </p>
        </div>
      </div>

      {/* Chat Popup Window */}
      <div className={`chat-widget ${isOpen ? 'open' : ''}`}>
        {/* Widget Header */}
        <div className="widget-header">
          <div className="widget-header-left">
            <div className="widget-avatar">🤖</div>
            <div>
              <div className="widget-title">AI Buddy</div>
              <div className="widget-status">
                <span className={`dot ${isOnline ? 'online' : 'offline'}`}></span>
                {isOnline ? 'Online' : 'Offline'}
              </div>
            </div>
          </div>
          <div className="widget-header-actions">
            {messages.length > 0 && (
              <button className="btn-icon" onClick={handleClear} title="Clear chat">
                🗑️
              </button>
            )}
            <button className="btn-icon btn-close" onClick={() => setIsOpen(false)} title="Close">
              ✕
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="widget-messages">
          {messages.length === 0 && !isLoading ? (
            <div className="widget-welcome">
              <div className="welcome-emoji">🤖</div>
              <h3>AI Buddy</h3>
              <p>Ask me about Kubernetes, Docker, CI/CD, logs & more!</p>
              <div className="quick-actions">
                {QUICK_ACTIONS.map((action, i) => (
                  <button
                    key={i}
                    className="quick-action-btn"
                    onClick={() => handleSend(action.query)}
                    disabled={!isOnline}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble key={i} {...msg} />
              ))}
              {isLoading && messages[messages.length - 1]?.content === '' && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <ChatInput onSend={handleSend} disabled={!isOnline || isLoading} />
      </div>

      {/* Floating Action Button */}
      <button
        className={`fab ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title={isOpen ? 'Close chat' : 'Open DevOps Assistant'}
      >
        <span className="fab-icon-open">🤖</span>
        <span className="fab-icon-close">✕</span>
      </button>
    </>
  );
}

export default App;
