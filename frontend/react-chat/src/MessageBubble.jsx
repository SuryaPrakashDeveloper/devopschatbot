function MessageBubble({ role, content, timestamp }) {
  const isUser = role === 'user';

  const formatTime = (ts) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Enhanced markdown rendering for DevOps AI responses
  const renderContent = (text) => {
    if (isUser) return text;

    let html = text;

    // Convert code blocks (```code```) to <pre>
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Convert **bold** to <strong>
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');

    // Convert inline `code` to <code>
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Convert ### headings
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');

    // Convert bullet points
    html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Convert numbered lists
    html = html.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');

    // Convert remaining newlines to <br>
    html = html.replace(/\n/g, '<br/>');

    // Clean up extra <br> after block elements
    html = html.replace(/<\/(pre|ul|ol|h[1-3])><br\/>/g, '</$1>');
    html = html.replace(/<br\/><(pre|ul|ol|h[1-3])>/g, '<$1>');

    return <span dangerouslySetInnerHTML={{ __html: html }} />;
  };

  return (
    <div className={`message ${isUser ? 'user' : 'ai'}`}>
      <div className="message-avatar">
        {isUser ? '🧑‍💻' : '🤖'}
      </div>
      <div>
        <div className="message-content">
          {renderContent(content)}
        </div>
        {timestamp && (
          <div className="message-time">{formatTime(timestamp)}</div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
