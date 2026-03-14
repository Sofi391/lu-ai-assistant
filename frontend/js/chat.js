document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = 'http://localhost:8000';
    const token = localStorage.getItem('lu_token');
    
    // Auth check
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    // Check if token is expired
    if (isTokenExpired(token)) {
        localStorage.removeItem('lu_token');
        window.location.href = 'login.html';
        return;
    }

    // DOM Elements
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const chatTitle = document.getElementById('chat-title');
    const newChatBtn = document.getElementById('new-chat-btn');
    const sessionsList = document.getElementById('sessions-list');
    const logoutBtn = document.getElementById('logout-btn');
    const ingestBtn = document.getElementById('ingest-btn');
    const charCount = document.getElementById('char-count');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const userEmail = document.getElementById('user-email');
    const userName = document.getElementById('user-name');
    const userInitials = document.getElementById('user-initials');
    const streamingOverlay = document.getElementById('streaming-overlay');
    const cancelStreamBtn = document.getElementById('cancel-stream-btn');
    const toastContainer = document.getElementById('toast-container');

    // State
    let currentSessionId = null;
    let isStreaming = false;
    let abortController = null;
    let reconnectAttempts = 0;
    let currentUser = null;
    const MAX_RECONNECT_ATTEMPTS = 3;

    // Constants
    const MAX_INPUT_LENGTH = 2000;

    // Initialize - Start with new chat page
    startNewChat();
    loadUserProfile();
    loadSessions();
    setupEventListeners();
    setupKeyboardShortcuts();

    function setupEventListeners() {
        sendButton.addEventListener('click', sendMessage);
        newChatBtn.addEventListener('click', startNewChat);
        logoutBtn.addEventListener('click', logout);

        // Ingest button click handler
        if (ingestBtn) {
            ingestBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Ingest button clicked, navigating to ingest.html');
                window.location.href = 'ingest.html';
            });
        }

        if (cancelStreamBtn) {
            cancelStreamBtn.addEventListener('click', cancelStreaming);
        }

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebar_collapsed', sidebar.classList.contains('collapsed'));
            });

            // Restore sidebar state
            if (localStorage.getItem('sidebar_collapsed') === 'true') {
                sidebar.classList.add('collapsed');
            }
        }

        // Input handling
        chatInput.addEventListener('input', handleInputChange);
        chatInput.addEventListener('keydown', handleKeyDown);

        // Auto-resize
        chatInput.addEventListener('input', autoResizeTextarea);

        // Suggestion card handlers
        document.querySelectorAll('.suggestion-card').forEach(card => {
            card.addEventListener('click', () => {
                const prompt = card.dataset.prompt;
                if (prompt) {
                    chatInput.value = prompt;
                    autoResizeTextarea();
                    handleInputChange();
                    chatInput.focus();
                }
            });
        });
    }

    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to focus input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                chatInput.focus();
            }

            // Escape to cancel streaming
            if (e.key === 'Escape' && isStreaming) {
                e.preventDefault();
                cancelStreaming();
            }
        });
    }

    function handleInputChange() {
        const length = chatInput.value.length;
        charCount.innerHTML = `<span class="current">${length}</span>/<span class="max">${MAX_INPUT_LENGTH}</span>`;

        // Visual feedback when approaching limit
        const currentSpan = charCount.querySelector('.current');
        if (length > MAX_INPUT_LENGTH * 0.9) {
            currentSpan.style.color = '#f59e0b';
        } else if (length >= MAX_INPUT_LENGTH) {
            currentSpan.style.color = '#ef4444';
        } else {
            currentSpan.style.color = 'var(--text-secondary)';
        }

        sendButton.disabled = length === 0 || length > MAX_INPUT_LENGTH || isStreaming;
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendButton.disabled) sendMessage();
        }
    }

    function autoResizeTextarea() {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
    }

    async function loadUserProfile() {
        try {
            const response = await fetch(`${API_BASE}/user/status/`, {
                headers: authHeaders()
            });

            if (response.status === 401) {
                handleAuthError();
                return;
            }

            if (response.ok) {
                const user = await response.json();
                currentUser = user;

                console.log('User status loaded:', user);

                // Update UI with user info from your backend
                if (userEmail) userEmail.textContent = user.username || '';

                // Use full_name from backend (user.first_name in your view)
                const displayName = user.full_name || user.username?.split('@')[0] || 'User';
                if (userName) userName.textContent = displayName;

                // Set user initials for avatar
                if (userInitials) {
                    const initials = getInitials(displayName);
                    userInitials.textContent = initials;
                }

                // Check if user is admin based on your is_admin field
                if (user.is_admin && ingestBtn) {
                    ingestBtn.style.display = 'flex';
                    ingestBtn.classList.add('visible');
                    console.log('✅ Ingest button shown for admin user');
                } else if (ingestBtn) {
                    ingestBtn.style.display = 'none';
                    console.log('❌ Ingest button hidden - user is not admin');
                }

                console.log(`User stats: ${user.session_count} sessions, ${user.message_count} messages`);
            }
        } catch (error) {
            console.error('Error loading user status:', error);
        }
    }

    function getInitials(name) {
        if (!name) return 'LU';

        const parts = name.split(' ');
        if (parts.length === 1) {
            return parts[0].substring(0, 2).toUpperCase();
        }
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }

    async function loadSessions() {
        try {
            sessionsList.innerHTML = `
                <div class="loading-sessions">
                    <div class="loading-spinner"></div>
                    <span>Loading conversations...</span>
                </div>
            `;

            const response = await fetch(`${API_BASE}/sessions/`, {
                headers: authHeaders()
            });

            if (response.status === 401) {
                handleAuthError();
                return;
            }

            if (!response.ok) {
                throw new Error(`Failed to load sessions: ${response.status}`);
            }

            const sessions = await response.json();
            renderSessions(sessions);
        } catch (error) {
            console.error('Error loading sessions:', error);
            sessionsList.innerHTML = '<div class="error-message">Failed to load conversations. <button onclick="location.reload()">Retry</button></div>';
        }
    }

    function renderSessions(sessions) {
        if (sessions.length === 0) {
            sessionsList.innerHTML = '<div class="empty-sessions">Start a new conversation</div>';
            return;
        }

        sessionsList.innerHTML = sessions.map(session => `
            <div class="session-item ${session.id === currentSessionId ? 'active' : ''}" data-id="${session.id}">
                <div class="session-title">${escapeHtml(session.title || 'New Conversation')}</div>
                <div class="session-date">${formatDate(session.created_at)}</div>
            </div>
        `).join('');

        sessionsList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => loadSession(item.dataset.id));
        });
    }

    async function loadSession(sessionId) {
        try {
            chatMessages.innerHTML = '<div class="loading-messages">Loading conversation...</div>';

            const response = await fetch(`${API_BASE}/session/${sessionId}/messages/`, {
                headers: authHeaders()
            });

            if (response.status === 401) {
                handleAuthError();
                return;
            }

            if (response.status === 404) {
                showError('Session not found');
                startNewChat();
                return;
            }

            if (!response.ok) {
                throw new Error(`Failed to load session: ${response.status}`);
            }

            const messages = await response.json();
            currentSessionId = sessionId;

            chatMessages.innerHTML = '';

            if (messages.length === 0) {
                showWelcomeMessage();
            } else {
                messages.forEach(msg => appendMessage(msg.role, msg.content, false));
            }

            // Update active state in sidebar
            const sessionItem = sessionsList.querySelector(`[data-id="${sessionId}"]`);
            if (sessionItem) {
                chatTitle.textContent = sessionItem.querySelector('.session-title').textContent;
                sessionsList.querySelectorAll('.session-item').forEach(item => item.classList.remove('active'));
                sessionItem.classList.add('active');
            }

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;

        } catch (error) {
            console.error('Error loading session:', error);
            showError('Failed to load conversation');
            startNewChat();
        }
    }

    function startNewChat() {
        // Cancel any ongoing stream
        if (isStreaming) {
            cancelStreaming();
        }

        currentSessionId = null;
        chatTitle.textContent = 'New conversation';
        showWelcomeMessage();

        // Remove active state from all sessions
        sessionsList.querySelectorAll('.session-item').forEach(item => item.classList.remove('active'));

        // Focus input
        chatInput.focus();
    }

    function showWelcomeMessage() {
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 16v-4M12 8h.01"/>
                    </svg>
                </div>
                <h2>How can I help you today?</h2>
                <p>Ask me anything about your documents. I'm here to help!</p>

                <div class="suggestion-grid">
                    <button class="suggestion-card" data-prompt="What documents do I have?">
                        <span class="suggestion-icon">📄</span>
                        <span class="suggestion-text">What documents do I have?</span>
                    </button>
                    <button class="suggestion-card" data-prompt="Summarize my recent uploads">
                        <span class="suggestion-icon">📊</span>
                        <span class="suggestion-text">Summarize my recent uploads</span>
                    </button>
                    <button class="suggestion-card" data-prompt="Find information about">
                        <span class="suggestion-icon">🔍</span>
                        <span class="suggestion-text">Find specific information</span>
                    </button>
                    <button class="suggestion-card" data-prompt="Explain how RAG works">
                        <span class="suggestion-icon">🤖</span>
                        <span class="suggestion-text">How does LU work?</span>
                    </button>
                </div>
            </div>
        `;

        // Re-attach suggestion card handlers
        document.querySelectorAll('.suggestion-card').forEach(card => {
            card.addEventListener('click', () => {
                const prompt = card.dataset.prompt;
                if (prompt) {
                    chatInput.value = prompt;
                    autoResizeTextarea();
                    handleInputChange();
                    chatInput.focus();
                }
            });
        });
    }

    async function sendMessage() {
        const question = chatInput.value.trim();

        // Validation
        if (!question || isStreaming) return;

        if (question.length > MAX_INPUT_LENGTH) {
            showError(`Message too long (max ${MAX_INPUT_LENGTH} characters)`);
            return;
        }

        // Reset reconnect attempts
        reconnectAttempts = 0;

        // Create abort controller for this request
        abortController = new AbortController();
        isStreaming = true;

        // Show streaming overlay
        if (streamingOverlay) {
            streamingOverlay.style.display = 'block';
        }

        // Update UI
        sendButton.disabled = true;
        chatInput.disabled = true;
        charCount.innerHTML = `<span class="current">0</span>/<span class="max">${MAX_INPUT_LENGTH}</span>`;

        // Add user message
        appendMessage('user', question);
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Create bot message placeholder
        const botMessageDiv = appendMessage('assistant', '', true);
        addTypingIndicator(botMessageDiv);

        const isFirstMessage = !currentSessionId;

        try {
            const response = await fetch(`${API_BASE}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    ...(currentSessionId && { 'X-Session-ID': currentSessionId })
                },
                body: JSON.stringify({
                    question,
                    ...(currentSessionId && { session_id: currentSessionId })
                }),
                signal: abortController.signal
            });

            // Handle HTTP errors
            if (!response.ok) {
                await handleHttpError(response, botMessageDiv);
                return;
            }

            // Get session ID from header if new session
            const newSessionId = response.headers.get('X-Session-ID');
            if (newSessionId) {
                currentSessionId = newSessionId;
            }

            // Check if response is stream or JSON
            const contentType = response.headers.get('Content-Type');

            if (contentType && contentType.includes('text/plain')) {
                // Handle streaming response
                await handleStreamingResponse(response, botMessageDiv);
            } else {
                // Handle JSON response (fallback)
                const data = await response.json();
                botMessageDiv.textContent = data.message || data.response || 'No response';
            }

            // Remove typing indicator
            removeTypingIndicator(botMessageDiv);

            // Handle first message - create session title and refresh list
            if (isFirstMessage && botMessageDiv.textContent) {
                const title = question.substring(0, 35) + (question.length > 35 ? '...' : '');
                chatTitle.textContent = title;
                await loadSessions();
            }

        } catch (error) {
            handleStreamingError(error, botMessageDiv);
        } finally {
            // Reset streaming state
            isStreaming = false;

            // Hide streaming overlay
            if (streamingOverlay) {
                streamingOverlay.style.display = 'none';
            }

            sendButton.disabled = false;
            chatInput.disabled = false;
            abortController = null;
            chatInput.focus();

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    async function handleStreamingResponse(response, botMessageDiv) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let receivedChunks = false;

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                receivedChunks = true;
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;

                // During streaming, show plain text for speed
                botMessageDiv.textContent = fullText;
                botMessageDiv.classList.add('streaming');

                // Auto-scroll
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            // Remove streaming class
            botMessageDiv.classList.remove('streaming');

            // Apply markdown formatting to the complete message
            if (fullText) {
                botMessageDiv.innerHTML = formatMarkdown(fullText);
            }

            // If no chunks received but response was OK, something went wrong
            if (!receivedChunks) {
                throw new Error('Empty stream response');
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                botMessageDiv.textContent = fullText + '\n\n[Stream cancelled]';
                showInfo('Message generation cancelled');
            } else {
                throw error;
            }
        }
    }

    async function handleHttpError(response, botMessageDiv) {
        let errorData;
        try {
            errorData = await response.json();
        } catch {
            errorData = { message: `Error: ${response.status}` };
        }

        removeTypingIndicator(botMessageDiv);

        switch (response.status) {
            case 400:
                botMessageDiv.textContent = errorData.message || 'Invalid request. Please check your input.';
                botMessageDiv.classList.add('error');
                break;

            case 401:
                handleAuthError();
                return;

            case 404:
                botMessageDiv.textContent = errorData.message || 'Session not found. Starting new conversation.';
                botMessageDiv.classList.add('error');
                currentSessionId = null;
                setTimeout(() => loadSessions(), 1000);
                break;

            case 429:
                const waitTime = errorData.wait || 60;
                botMessageDiv.textContent = `Rate limit exceeded. Please wait ${waitTime} seconds before sending another message.`;
                botMessageDiv.classList.add('error');

                // Disable input for wait time
                chatInput.disabled = true;
                sendButton.disabled = true;
                setTimeout(() => {
                    chatInput.disabled = false;
                    sendButton.disabled = false;
                    chatInput.focus();
                }, waitTime * 1000);
                break;

            case 500:
                botMessageDiv.textContent = errorData.message || 'Server error. Please try again later.';
                botMessageDiv.classList.add('error');
                break;

            default:
                botMessageDiv.textContent = errorData.message || 'An unexpected error occurred.';
                botMessageDiv.classList.add('error');
        }
    }

    function handleStreamingError(error, botMessageDiv) {
        console.error('Chat error:', error);

        removeTypingIndicator(botMessageDiv);

        if (error.name === 'AbortError') {
            botMessageDiv.textContent = 'Message cancelled.';
            botMessageDiv.classList.add('info');
        } else if (error.message.includes('Failed to fetch')) {
            // Network error - attempt reconnect
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                botMessageDiv.textContent = `Connection lost. Reconnecting... (Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`;
                botMessageDiv.classList.add('info');

                // Auto-retry
                setTimeout(() => {
                    if (!isStreaming) {
                        sendMessage();
                    }
                }, 2000 * reconnectAttempts);
            } else {
                botMessageDiv.textContent = 'Unable to connect to server. Please check your network connection.';
                botMessageDiv.classList.add('error');
            }
        } else {
            botMessageDiv.textContent = 'Connection error. Please check your network and try again.';
            botMessageDiv.classList.add('error');
        }
    }

    function cancelStreaming() {
        if (abortController) {
            abortController.abort();
            isStreaming = false;

            if (streamingOverlay) {
                streamingOverlay.style.display = 'none';
            }

            sendButton.disabled = false;
            chatInput.disabled = false;
            showInfo('Message generation cancelled');
        }
    }

    function appendMessage(role, content, isPlaceholder = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        if (isPlaceholder) {
            messageDiv.classList.add('placeholder');
        }

        if (content) {
            // Always format markdown for assistant messages
            if (role === 'assistant') {
                messageDiv.innerHTML = formatMarkdown(content);
            } else {
                // User messages remain as plain text
                messageDiv.textContent = content;
            }
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageDiv;
    }

    function formatMarkdown(text) {
        if (!text) return '';

        // Escape HTML first to prevent XSS
        text = text.replace(/&/g, '&amp;')
                   .replace(/</g, '&lt;')
                   .replace(/>/g, '&gt;')
                   .replace(/"/g, '&quot;')
                   .replace(/'/g, '&#039;');

        // Headers (must come before other replacements)
        text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>')
                   .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                   .replace(/^# (.*$)/gm, '<h1>$1</h1>');

        // Bold
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                   .replace(/__(.*?)__/g, '<strong>$1</strong>');

        // Italic
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')
                   .replace(/_(.*?)_/g, '<em>$1</em>');

        // Code blocks
        text = text.replace(/```([\s\S]*?)```/g, function(match, code) {
            return '<pre><code>' + code.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</code></pre>';
        });

        // Inline code
        text = text.replace(/`(.*?)`/g, function(match, code) {
            return '<code>' + code.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</code>';
        });

        // Lists (unordered)
        text = text.replace(/^\* (.*$)/gm, '<li>$1</li>')
                   .replace(/^- (.*$)/gm, '<li>$1</li>')
                   .replace(/^\+ (.*$)/gm, '<li>$1</li>');

        // Wrap consecutive list items in <ul>
        text = text.replace(/(<li>.*<\/li>\n?)+/g, function(match) {
            return '<ul>' + match.replace(/\n/g, '') + '</ul>';
        });

        // Lists (ordered)
        text = text.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>\n?)+/g, function(match) {
            if (match.includes('<ul>')) return match;
            return '<ol>' + match.replace(/\n/g, '') + '</ol>';
        });

        // Blockquotes
        text = text.replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>');

        // Links
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

        // Line breaks (preserve paragraphs)
        text = text.replace(/\n\n/g, '</p><p>');
        text = text.replace(/\n/g, '<br>');

        // Wrap in paragraph if not already wrapped
        if (!text.startsWith('<h') && !text.startsWith('<p>') && !text.startsWith('<ul>') && !text.startsWith('<ol>') && !text.startsWith('<blockquote>')) {
            text = '<p>' + text + '</p>';
        }

        return text;
    }

    function addTypingIndicator(messageDiv) {
        messageDiv.classList.add('typing');
        messageDiv.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    }

    function removeTypingIndicator(messageDiv) {
        messageDiv.classList.remove('typing');
    }

    function showError(message) {
        createToast(message, 'error');
    }

    function showInfo(message) {
        createToast(message, 'info');
    }

    function createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 4000);
    }

    function handleAuthError() {
        localStorage.removeItem('lu_token');
        showError('Session expired. Please login again.');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1500);
    }

    function authHeaders() {
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    function logout() {
        localStorage.removeItem('lu_token');
        window.location.href = 'login.html';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';

        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) {
            // Today - show time
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        return date.toLocaleDateString();
    }

    function isTokenExpired(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const expiry = payload.exp * 1000;
            return Date.now() >= expiry;
        } catch {
            return true;
        }
    }
});