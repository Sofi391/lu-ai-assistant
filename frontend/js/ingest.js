const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('lu_token');
    
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
    const contentInput = document.getElementById('content-input');
    const ingestSubmitBtn = document.getElementById('ingest-submit-btn');
    const clearBtn = document.getElementById('clear-btn');
    const statusMessage = document.getElementById('ingest-status');
    const charCount = document.getElementById('content-char-count');
    const backToChatBtn = document.getElementById('back-to-chat');
    const loadingOverlay = document.getElementById('loading-overlay');

    // Check if user is admin before allowing access to ingest page
    checkAdminStatus();

    // Event Listeners
    contentInput.addEventListener('input', updateCharCount);
    ingestSubmitBtn.addEventListener('click', handleIngest);
    clearBtn.addEventListener('click', clearContent);

    if (backToChatBtn) {
    backToChatBtn.addEventListener('click', () => {
        window.location.href = 'chat.html';
    });
}

    async function checkAdminStatus() {
        try {
            const response = await fetch(`${API_BASE}/user/status/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401) {
                handleAuthError();
                return;
            }

            if (response.ok) {
                const user = await response.json();

                // Check if user is admin based on your is_admin field
                if (!user.is_admin) {
                    showStatus('Access denied. Admin privileges required.', 'error');
                    setTimeout(() => {
                        window.location.href = 'chat.html';
                    }, 2000);
                }
            } else {
                throw new Error('Failed to verify admin status');
            }
        } catch (error) {
            console.error('Error checking admin status:', error);
            showStatus('Failed to verify permissions. Redirecting...', 'error');
            setTimeout(() => {
                window.location.href = 'chat.html';
            }, 2000);
        }
    }

    function updateCharCount() {
        const length = contentInput.value.length;
        charCount.textContent = `${length.toLocaleString()} characters`;

        // Disable submit if empty
        ingestSubmitBtn.disabled = length === 0;

        // Visual feedback for large inputs
        if (length > 10000) {
            charCount.style.color = '#f59e0b';
        } else if (length > 50000) {
            charCount.style.color = '#ef4444';
        } else {
            charCount.style.color = 'var(--text-secondary)';
        }
    }

    function clearContent() {
        contentInput.value = '';
        updateCharCount();
        hideStatus();

        // Focus back on textarea
        contentInput.focus();
    }

    async function handleIngest() {
        const content = contentInput.value.trim();

        if (!content) {
            showStatus('Please provide content to ingest', 'error');
            return;
        }

        // Optional: Add size validation
        if (content.length > 100000) {
            showStatus('Content too large. Please limit to 100,000 characters.', 'error');
            return;
        }

        setLoading(true);
        hideStatus();

        try {
            const response = await fetch(`${API_BASE}/ingest/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ content })
            });

            // Handle 401 Unauthorized
            if (response.status === 401) {
                handleAuthError();
                return;
            }

            // Handle 403 Forbidden - User not admin
            if (response.status === 403) {
                showStatus('⛔ Access denied. Admin privileges required.', 'error');
                setTimeout(() => {
                    window.location.href = 'chat.html';
                }, 2000);
                return;
            }

            // Handle 429 Rate Limit
            if (response.status === 429) {
                let waitTime = 60;
                try {
                    const error = await response.json();
                    waitTime = error.wait ? Math.ceil(error.wait) : 60;
                } catch {
                    // Use default wait time
                }
                showStatus(`⏱️ Rate limit exceeded. Please wait ${waitTime} seconds`, 'error');
                return;
            }

            // Handle 400 Bad Request
            if (response.status === 400) {
                const error = await response.json();
                showStatus(`❌ ${error.message || 'Invalid content provided'}`, 'error');
                return;
            }

            // Handle 500 Internal Server Error
            if (response.status === 500) {
                const error = await response.json();
                showStatus(`❌ Server error: ${error.message || 'Failed to ingest content'}`, 'error');
                return;
            }

            // Handle other non-OK responses
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            // Success!
            const data = await response.json();
            showStatus('✅ Content successfully ingested into knowledge base!', 'success');

            // Clear the textarea after successful ingestion
            setTimeout(() => {
                clearContent();
            }, 2000);

        } catch (error) {
            console.error('Ingest error:', error);

            // Handle network errors
            if (error.message.includes('Failed to fetch')) {
                showStatus('🌐 Cannot connect to server. Please check your network.', 'error');
            } else {
                showStatus(`❌ ${error.message || 'Connection error. Please try again'}`, 'error');
            }
        } finally {
            setLoading(false);
        }
    }

    function setLoading(loading) {
        const btnText = ingestSubmitBtn.querySelector('.btn-text');
        const btnLoading = ingestSubmitBtn.querySelector('.btn-loading');

        if (loading) {
            ingestSubmitBtn.disabled = true;
            clearBtn.disabled = true;
            contentInput.disabled = true;
            if (btnText) btnText.style.display = 'none';
            if (btnLoading) btnLoading.style.display = 'inline';

            // Show loading overlay if exists
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
            }
        } else {
            ingestSubmitBtn.disabled = contentInput.value.trim().length === 0;
            clearBtn.disabled = false;
            contentInput.disabled = false;
            if (btnText) btnText.style.display = 'inline';
            if (btnLoading) btnLoading.style.display = 'none';

            // Hide loading overlay
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    }

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 5000);
        }
    }

    function hideStatus() {
        statusMessage.style.display = 'none';
    }

    function handleAuthError() {
        localStorage.removeItem('lu_token');
        showStatus('Session expired. Redirecting to login...', 'error');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1500);
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

    // Initialize
    updateCharCount();
    contentInput.focus();
});