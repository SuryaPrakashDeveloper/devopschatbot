import { useState, useEffect, useRef, useCallback } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import ChatInput from './ChatInput';
import { checkApiStatus, sendMessage, clearSession } from './api';

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

    try {
      const data = await sendMessage(text, sessionId);
      const aiMsg = { role: 'ai', content: data.response, timestamp: new Date() };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      const errMsg = {
        role: 'ai',
        content: `⚠️ Error: ${err.message}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, sessionId]);

  const handleClear = useCallback(async () => {
    await clearSession(sessionId);
    setMessages([]);
  }, [sessionId]);

  return (
    <>
      {/* Chat Popup Window */}
      <div className={`chat-widget ${isOpen ? 'open' : ''}`}>
        {/* Widget Header */}
        <div className="widget-header">
          <div className="widget-header-left">
            <div className="widget-avatar">☸️</div>
            <div>
              <div className="widget-title">DevOps Assistant</div>
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
              <div className="welcome-emoji">☸️</div>
              <h3>DevOps Assistant</h3>
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
              {isLoading && <TypingIndicator />}
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
        <span className="fab-icon-open">☸️</span>
        <span className="fab-icon-close">✕</span>
      </button>
    </>
  );
}

export default App;
