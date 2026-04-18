
function MessageBubble({ role, content, timestamp }) {
  const isUser = role === 'user';

  const formatTime = (ts) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Sanitize HTML to prevent XSS from LLM output
  const sanitizeHTML = (html) => {
    // Remove dangerous tags entirely
    html = html.replace(/<\s*(script|iframe|object|embed|form|link|meta|base|applet)[^>]*>[\s\S]*?<\/\s*\1\s*>/gi, '');
    html = html.replace(/<\s*(script|iframe|object|embed|form|link|meta|base|applet)[^>]*\/?>/gi, '');
    // Remove event handler attributes (onclick, onerror, onload, etc.)
    html = html.replace(/\s+on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '');
    // Remove javascript: URLs (but keep our onclick on copy buttons)
    html = html.replace(/href\s*=\s*["']?\s*javascript\s*:/gi, 'href="');
    return html;
  };

  // Enhanced markdown rendering for DevOps AI responses
  const renderContent = (text) => {
    if (isUser) return text;
    if (!text) return '';

    let html = text;

    // Sanitize raw LLM output FIRST — before we add our own HTML (copy buttons etc.)
    html = sanitizeHTML(html);

    // Convert code blocks (```lang\ncode```) to <pre> with copy button and language label
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
      const langLabel = lang || 'code';
      const escapedCode = code.trim()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
      const copyId = `code-${Math.random().toString(36).slice(2, 8)}`;
      return `<div class="code-block-wrapper">
        <div class="code-block-header">
          <span class="code-lang">${langLabel}</span>
          <button class="code-copy-btn" data-code-id="${copyId}" onclick="
            const codeEl = document.getElementById('${copyId}');
            navigator.clipboard.writeText(codeEl.textContent).then(() => {
              this.textContent = '✅ Copied!';
              setTimeout(() => { this.textContent = '📋 Copy'; }, 2000);
            });
          ">📋 Copy</button>
        </div>
        <pre><code id="${copyId}">${escapedCode}</code></pre>
      </div>`;
    });

    // Convert markdown tables to HTML tables
    html = html.replace(/((?:\|[^\n]+\|\n?)+)/g, (tableBlock) => {
      const rows = tableBlock.trim().split('\n').filter(r => r.trim());
      if (rows.length < 2) return tableBlock;

      // Check if second row is separator (|---|---|)
      const isSeparator = /^\|[\s\-:|\s]+\|$/.test(rows[1]?.trim());
      if (!isSeparator) return tableBlock;

      let tableHtml = '<table class="md-table">';

      // Header row
      const headerCells = rows[0].split('|').filter(c => c.trim() !== '');
      tableHtml += '<thead><tr>';
      headerCells.forEach(cell => {
        tableHtml += `<th>${cell.trim()}</th>`;
      });
      tableHtml += '</tr></thead>';

      // Body rows (skip separator row at index 1)
      tableHtml += '<tbody>';
      for (let i = 2; i < rows.length; i++) {
        const cells = rows[i].split('|').filter(c => c.trim() !== '');
        tableHtml += '<tr>';
        cells.forEach(cell => {
          tableHtml += `<td>${cell.trim()}</td>`;
        });
        tableHtml += '</tr>';
      }
      tableHtml += '</tbody></table>';

      return tableHtml;
    });

    // Convert **bold** to <strong>
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');

    // Convert inline `code` to <code> (but not inside <pre> blocks)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Convert ### headings
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');

    // Convert horizontal rules
    html = html.replace(/^---+$/gm, '<hr/>');

    // Convert bullet points
    html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Convert numbered lists
    html = html.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');

    // Convert [text](url) links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Convert remaining newlines to <br>
    html = html.replace(/\n/g, '<br/>');

    // Clean up extra <br> after block elements
    html = html.replace(/<\/(pre|ul|ol|h[1-3]|table|hr|div)><br\/>/g, '</$1>');
    html = html.replace(/<br\/><(pre|ul|ol|h[1-3]|table|hr|div)/g, '<$1');


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
