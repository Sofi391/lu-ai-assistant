document.addEventListener('DOMContentLoaded', () => {
    const chatToggle = document.getElementById('chat-toggle');
    const chatWidget = document.getElementById('chat-widget');
    const closeChat = document.getElementById('close-chat');
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    // --- Auth Check ---
    const token = localStorage.getItem('lu_token');
    if (!token) {
        // If they aren't logged in, they can't see the chatbot or landing page features
        window.location.href = 'login.html';
    }

    // --- Load Chat History ---
    const loadHistory = async () => {
        try {
            const response = await fetch('http://localhost:8000/history', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const history = await response.json();
                history.forEach(item => {
                    appendMessage('user', item.question);
                    appendMessage('bot', item.answer);
                });
            }
        } catch (err) {
            console.error("Failed to load history:", err);
        }
    };
    loadHistory();

    // Toggle Chat Visibility
    chatToggle.addEventListener('click', () => {
        chatWidget.classList.toggle('active');
    });

    closeChat.addEventListener('click', () => {
        chatWidget.classList.remove('active');
    });

    // Handle Sending Message
    const sendMessage = async () => {
        const text = userInput.value.trim();
        if (!text) return;

        // Append User Message
        appendMessage('user', text);
        userInput.value = '';

        // Show Loading (Thinking) State
        const loadingDiv = appendMessage('bot', 'LU is thinking...');
        
        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ question: text }),
            });

            if (!response.ok) {
                if(response.status === 401) window.location.href = 'login.html';
                throw new Error('Backend error');
            }

            const data = await response.json();
            
            // Clear loading and show real response
            loadingDiv.textContent = data.response;
            
        } catch (error) {
            loadingDiv.textContent = "I'm having trouble connecting to my brain right now. Please check if the server is running!";
            console.error('Chat Error:', error);
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function appendMessage(type, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }
});
