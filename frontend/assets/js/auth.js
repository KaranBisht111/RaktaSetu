document.addEventListener('DOMContentLoaded', () => {

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const backendUrl = 'http://127.0.0.1:5000';

    // --- LOGIN FORM ---
    if (loginForm) {
        const loginBtn = document.getElementById('login-btn');

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            setLoading(loginBtn, true, 'Logging in...');

            const role = document.getElementById('role').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            if (!role || !email || !password) {
                displayMessage('Please fill in all fields.', 'danger');
                setLoading(loginBtn, false, 'Login');
                return;
            }

            try {
                const response = await fetch(`${backendUrl}/api/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role, email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    localStorage.setItem('token', data.token);
                    displayMessage('Login successful! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = getRedirectPath(data.role);
                    }, 1500);
                } else {
                    displayMessage(data.message || 'Login failed!', 'danger');
                    setLoading(loginBtn, false, 'Login');
                }
            } catch (error) {
                console.error('Login Error:', error);
                displayMessage('Server connection failed. Ensure backend is running.', 'danger');
                setLoading(loginBtn, false, 'Login');
            }
        });
    }

    // --- REGISTER FORM ---
    if (registerForm) {
        const registerBtn = document.getElementById('register-btn');

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            setLoading(registerBtn, true, 'Registering...');

            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

            if (password !== confirmPassword) {
                displayMessage('Passwords do not match.', 'danger');
                setLoading(registerBtn, false, 'Register');
                return;
            }

            const role = document.getElementById('role').value;
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;

            let requestBody = { role, name, email, password };
            if (role === 'donor') {
                requestBody.bloodType = document.getElementById('bloodType').value;
            }

            try {
                const response = await fetch(`${backendUrl}/api/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();

                if (response.ok) {
                    displayMessage('Registration successful! Please login.', 'success');
                    setTimeout(() => { window.location.href = 'login.html'; }, 2000);
                } else {
                    displayMessage(data.message || 'Registration failed!', 'danger');
                    setLoading(registerBtn, false, 'Register');
                }
            } catch (error) {
                console.error('Registration Error:', error);
                displayMessage('Server connection failed. Ensure backend is running.', 'danger');
                setLoading(registerBtn, false, 'Register');
            }
        });
    }

    // --- HELPER FUNCTIONS ---
    function setLoading(button, isLoading, text) {
        button.disabled = isLoading;
        button.innerHTML = isLoading 
            ? `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${text}`
            : text;
    }

    function displayMessage(message, type) {
        const container = document.getElementById('message-container');
        if (container) {
            container.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
        }
    }

    function getRedirectPath(role) {
        switch (role) {
            case 'donor': return 'donor.html';
            case 'hospital': return 'hospital.html';
            case 'admin': return 'admin.html';
            case 'bank': return 'marketplace.html';
            default: return 'index.html';
        }
    }
});
