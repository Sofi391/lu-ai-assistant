document.addEventListener('DOMContentLoaded', () => {
    let isLogin = true;
    const token = localStorage.getItem('lu_token');
    if (token) window.location.href = 'index.html';

    const toggleAuth = document.getElementById('toggle-auth');
    const authTitle = document.getElementById('auth-title');
    const nameGroup = document.getElementById('name-group');
    const submitBtn = document.getElementById('submit-btn');
    const toggleText = document.getElementById('toggle-text');

    toggleAuth.addEventListener('click', () => {
        isLogin = !isLogin;
        authTitle.textContent = isLogin ? 'Welcome Back' : 'Create Account';
        submitBtn.textContent = isLogin ? 'Login' : 'Sign Up';
        nameGroup.style.display = isLogin ? 'none' : 'block';
        toggleText.textContent = isLogin ? 'Sign Up' : 'Login';
        document.getElementById('toggle-auth').innerHTML = isLogin ? 
            "Don't have an account? <span>Sign Up</span>" : 
            "Already have an account? <span>Login</span>";
    });

    document.getElementById('auth-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const statusDiv = document.getElementById('auth-status');
        
        try {
            if (isLogin) {
                const response = await fetch('http://localhost:8000/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: email, password: password })
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('lu_token', data.access);
                    window.location.href = 'index.html';
                } else {
                    throw new Error('Invalid credentials');
                }
            } else {
                const fullName = document.getElementById('full_name').value;
                const response = await fetch('http://localhost:8000/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, full_name: fullName })
                });

                if (response.ok) {
                    statusDiv.textContent = "Account created! Now login.";
                    statusDiv.style.color = "#4ade80";
                    if (!isLogin) toggleAuth.click();
                } else {
                    throw new Error('Signup failed');
                }
            }
        } catch (err) {
            statusDiv.textContent = err.message;
            statusDiv.style.color = "#f87171";
        }
    });
});
