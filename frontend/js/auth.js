const API_BASE = 'http://localhost:8000';

// Login Handler
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('login-btn');

    if (!email || !password) {
        showError('Please fill in all fields');
        return;
    }

    setLoading(loginBtn, true);
    hideMessages();

    try {
        // Simple JWT expects form-urlencoded with username field
        const formData = new URLSearchParams();
        formData.append('username', email); // Backend uses username field with email value
        formData.append('password', password);

        const response = await fetch(`${API_BASE}/token/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Store tokens
            localStorage.setItem('lu_token', data.access);
            if (data.refresh) {
                localStorage.setItem('lu_refresh', data.refresh);
            }
            showSuccess('Login successful! Redirecting...');
            setTimeout(() => {
                window.location.href = 'chat.html';
            }, 500);
        } else {
            // Handle error responses
            if (response.status === 401) {
                showError('Invalid email or password');
            } else {
                showError(data.detail || 'Login failed. Please try again');
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Connection error. Please check your network');
    } finally {
        setLoading(loginBtn, false);
    }
}

// Signup Handler
async function handleSignup(e) {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const fullName = document.getElementById('full_name').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const signupBtn = document.getElementById('signup-btn');

    hideMessages();

    // Validation
    if (!email || !password) {
        showError('Email and password are required');
        return;
    }

    if (password.length < 8) {
        showError('Password must be at least 8 characters');
        return;
    }

    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    setLoading(signupBtn, true);

    try {
        // Your signup view expects JSON with email, password, full_name
        const response = await fetch(`${API_BASE}/signup/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password,
                full_name: fullName
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Success response from your view: {"msg": "User created successfully"}
            showSuccess(data.msg || 'Account created successfully! Redirecting to login...');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1500);
        } else {
            // Error responses from your view
            if (response.status === 400) {
                showError(data.error || 'User already exists or invalid data');
            } else if (response.status === 500) {
                showError(data.error || 'Server error. Please try again later');
            } else {
                showError('Signup failed. Please try again');
            }
        }
    } catch (error) {
        console.error('Signup error:', error);
        showError('Connection error. Please check your network');
    } finally {
        setLoading(signupBtn, false);
    }
}

// Helper Functions
function setLoading(button, loading) {
    const btnText = button.querySelector('.btn-text');
    const btnLoading = button.querySelector('.btn-loading');

    if (btnText && btnLoading) {
        if (loading) {
            button.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline';
        } else {
            button.disabled = false;
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorDiv.style.display === 'block') {
                errorDiv.style.display = 'none';
            }
        }, 5000);
    }
}

function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (successDiv.style.display === 'block') {
                successDiv.style.display = 'none';
            }
        }, 5000);
    }
}

function hideMessages() {
    const errorDiv = document.getElementById('error-message');
    const successDiv = document.getElementById('success-message');

    if (errorDiv) errorDiv.style.display = 'none';
    if (successDiv) successDiv.style.display = 'none';
}

// Optional: Add logout function for later use
function logout() {
    localStorage.removeItem('lu_token');
    localStorage.removeItem('lu_refresh');
    window.location.href = 'index.html';
}

// Optional: Check if token is expired (for protected pages)
function isTokenExpired(token) {
    if (!token) return true;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expiry = payload.exp * 1000; // Convert to milliseconds
        return Date.now() >= expiry;
    } catch {
        return true;
    }
}

// Optional: Add token to fetch requests (for API calls)
function authFetch(url, options = {}) {
    const token = localStorage.getItem('lu_token');

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
        },
    });
}