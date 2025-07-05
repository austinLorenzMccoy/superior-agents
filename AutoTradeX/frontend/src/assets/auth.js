/**
 * AutoTradeX Authentication System
 * Provides both mock authentication and real backend integration
 */

// Configuration
const AUTH_CONFIG = {
    // API endpoints
    apiBaseUrl: 'https://autotradex.onrender.com/api',
    loginEndpoint: '/auth/login',
    signupEndpoint: '/auth/signup',
    verifyTokenEndpoint: '/auth/verify',
    
    // Local storage keys
    tokenKey: 'autotradex_token',
    userKey: 'autotradex_user',
    
    // Mock users for offline/demo mode
    mockUsers: [
        { email: 'demo@example.com', password: 'password123', name: 'Demo User' },
        { email: 'test@example.com', password: 'password123', name: 'Test User' }
    ],
    
    // Settings
    useMockAuth: true, // Set to false to use only real backend
    tokenExpiry: 24 * 60 * 60 * 1000, // 24 hours in milliseconds
};

/**
 * Authentication API - handles both mock and real authentication
 */
const AuthAPI = {
    /**
     * Attempt to login a user
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise} - Resolves with user data or rejects with error
     */
    login: async function(email, password) {
        // Try real backend first if available
        if (!AUTH_CONFIG.useMockAuth) {
            try {
                const response = await fetch(`${AUTH_CONFIG.apiBaseUrl}${AUTH_CONFIG.loginEndpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Login failed');
                }
                
                const data = await response.json();
                return data;
            } catch (error) {
                console.warn('Real backend login failed, falling back to mock:', error);
                // Fall back to mock auth if real backend fails
                if (!AUTH_CONFIG.useMockAuth) throw error;
            }
        }
        
        // Mock authentication
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                const user = AUTH_CONFIG.mockUsers.find(u => 
                    u.email === email && u.password === password);
                
                if (user) {
                    // Create mock token
                    const token = btoa(`${user.email}:${Date.now()}`);
                    resolve({
                        token,
                        user: {
                            email: user.email,
                            name: user.name
                        }
                    });
                } else {
                    reject(new Error('Invalid email or password'));
                }
            }, 500); // Simulate network delay
        });
    },
    
    /**
     * Register a new user
     * @param {Object} userData - User registration data
     * @returns {Promise} - Resolves with user data or rejects with error
     */
    signup: async function(userData) {
        // Try real backend first if available
        if (!AUTH_CONFIG.useMockAuth) {
            try {
                const response = await fetch(`${AUTH_CONFIG.apiBaseUrl}${AUTH_CONFIG.signupEndpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Registration failed');
                }
                
                const data = await response.json();
                return data;
            } catch (error) {
                console.warn('Real backend signup failed, falling back to mock:', error);
                // Fall back to mock auth if real backend fails
                if (!AUTH_CONFIG.useMockAuth) throw error;
            }
        }
        
        // Mock registration
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                // Check if user already exists
                const existingUser = AUTH_CONFIG.mockUsers.find(u => u.email === userData.email);
                if (existingUser) {
                    reject(new Error('User with this email already exists'));
                    return;
                }
                
                // Create new mock user
                const newUser = {
                    email: userData.email,
                    password: userData.password,
                    name: userData.name || userData.email.split('@')[0]
                };
                
                // Add to mock users (in a real app, this would persist)
                AUTH_CONFIG.mockUsers.push(newUser);
                
                // Create mock token
                const token = btoa(`${newUser.email}:${Date.now()}`);
                resolve({
                    token,
                    user: {
                        email: newUser.email,
                        name: newUser.name
                    }
                });
            }, 800); // Simulate network delay
        });
    },
    
    /**
     * Verify authentication token
     * @param {string} token - Authentication token
     * @returns {Promise} - Resolves with user data if valid
     */
    verifyToken: async function(token) {
        // Try real backend first if available
        if (!AUTH_CONFIG.useMockAuth) {
            try {
                const response = await fetch(`${AUTH_CONFIG.apiBaseUrl}${AUTH_CONFIG.verifyTokenEndpoint}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Invalid token');
                }
                
                const data = await response.json();
                return data.user;
            } catch (error) {
                console.warn('Real backend token verification failed, falling back to mock:', error);
                // Fall back to mock auth if real backend fails
                if (!AUTH_CONFIG.useMockAuth) throw error;
            }
        }
        
        // Mock token verification
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                try {
                    // Decode token (in a real app, use proper JWT verification)
                    const tokenData = atob(token).split(':');
                    const email = tokenData[0];
                    const timestamp = parseInt(tokenData[1]);
                    
                    // Check if token is expired
                    if (Date.now() - timestamp > AUTH_CONFIG.tokenExpiry) {
                        reject(new Error('Token expired'));
                        return;
                    }
                    
                    // Find user
                    const user = AUTH_CONFIG.mockUsers.find(u => u.email === email);
                    if (!user) {
                        reject(new Error('User not found'));
                        return;
                    }
                    
                    resolve({
                        email: user.email,
                        name: user.name
                    });
                } catch (e) {
                    reject(new Error('Invalid token'));
                }
            }, 300);
        });
    },
    
    /**
     * Log out the current user
     */
    logout: function() {
        localStorage.removeItem(AUTH_CONFIG.tokenKey);
        localStorage.removeItem(AUTH_CONFIG.userKey);
    }
};

/**
 * Authentication Session Manager
 */
const AuthSession = {
    /**
     * Get the current authenticated user
     * @returns {Object|null} - User object or null if not authenticated
     */
    getCurrentUser: function() {
        const userJson = localStorage.getItem(AUTH_CONFIG.userKey);
        return userJson ? JSON.parse(userJson) : null;
    },
    
    /**
     * Get the authentication token
     * @returns {string|null} - Token or null if not authenticated
     */
    getToken: function() {
        return localStorage.getItem(AUTH_CONFIG.tokenKey);
    },
    
    /**
     * Set the current session
     * @param {Object} authData - Authentication data with token and user
     */
    setSession: function(authData) {
        localStorage.setItem(AUTH_CONFIG.tokenKey, authData.token);
        localStorage.setItem(AUTH_CONFIG.userKey, JSON.stringify(authData.user));
    },
    
    /**
     * Check if user is authenticated
     * @returns {boolean} - True if authenticated
     */
    isAuthenticated: function() {
        return !!this.getToken();
    },
    
    /**
     * Initialize authentication - verify token if exists
     * @returns {Promise} - Resolves when complete
     */
    init: async function() {
        const token = this.getToken();
        if (!token) return false;
        
        try {
            const user = await AuthAPI.verifyToken(token);
            this.setSession({ token, user });
            return true;
        } catch (error) {
            console.warn('Token verification failed:', error);
            this.logout();
            return false;
        }
    },
    
    /**
     * Log in a user
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise} - Resolves with user data
     */
    login: async function(email, password) {
        const authData = await AuthAPI.login(email, password);
        this.setSession(authData);
        return authData.user;
    },
    
    /**
     * Register a new user
     * @param {Object} userData - User registration data
     * @returns {Promise} - Resolves with user data
     */
    signup: async function(userData) {
        const authData = await AuthAPI.signup(userData);
        this.setSession(authData);
        return authData.user;
    },
    
    /**
     * Log out the current user
     */
    logout: function() {
        AuthAPI.logout();
        window.location.href = '/frontend/';
    }
};

// Initialize authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    AuthSession.init().then(isAuthenticated => {
        if (isAuthenticated) {
            console.log('User authenticated:', AuthSession.getCurrentUser());
            // Update UI for authenticated user
            updateAuthUI(true);
        }
    });
});

/**
 * Update UI based on authentication status
 * @param {boolean} isAuthenticated - Whether user is authenticated
 */
function updateAuthUI(isAuthenticated) {
    const loginBtn = document.querySelector('.login-btn');
    const signupBtn = document.querySelector('.signup-btn');
    
    if (isAuthenticated) {
        const user = AuthSession.getCurrentUser();
        
        // If login/signup buttons exist, replace with user info
        if (loginBtn) {
            const userMenu = document.createElement('div');
            userMenu.className = 'user-menu';
            userMenu.innerHTML = `
                <span class="user-name">Welcome, ${user.name || user.email}</span>
                <button class="btn btn-outline logout-btn">Log Out</button>
            `;
            loginBtn.parentNode.replaceChild(userMenu, loginBtn);
            
            // Add logout handler
            document.querySelector('.logout-btn').addEventListener('click', function() {
                AuthSession.logout();
            });
        }
        
        // Hide signup button if it exists
        if (signupBtn) {
            signupBtn.style.display = 'none';
        }
    }
}

/**
 * Show authentication modal for login or signup
 * @param {string} type - 'login' or 'signup'
 */
function showAuthModal(type) {
    // Remove any existing modal
    const existingModal = document.querySelector('.auth-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal container
    const modal = document.createElement('div');
    modal.className = 'auth-modal';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'auth-modal-content';
    
    // Create close button
    const closeBtn = document.createElement('span');
    closeBtn.className = 'auth-modal-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', function() {
        modal.remove();
    });
    
    // Create form
    const form = document.createElement('form');
    form.className = 'auth-form';
    
    // Create title
    const title = document.createElement('h2');
    title.textContent = type === 'login' ? 'Log In' : 'Sign Up';
    
    // Create email field
    const emailGroup = document.createElement('div');
    emailGroup.className = 'form-group';
    
    const emailLabel = document.createElement('label');
    emailLabel.textContent = 'Email';
    emailLabel.setAttribute('for', 'email');
    
    const emailInput = document.createElement('input');
    emailInput.type = 'email';
    emailInput.id = 'email';
    emailInput.placeholder = 'Enter your email';
    emailInput.required = true;
    
    emailGroup.appendChild(emailLabel);
    emailGroup.appendChild(emailInput);
    
    // Create password field
    const passwordGroup = document.createElement('div');
    passwordGroup.className = 'form-group';
    
    const passwordLabel = document.createElement('label');
    passwordLabel.textContent = 'Password';
    passwordLabel.setAttribute('for', 'password');
    
    const passwordInput = document.createElement('input');
    passwordInput.type = 'password';
    passwordInput.id = 'password';
    passwordInput.placeholder = 'Enter your password';
    passwordInput.required = true;
    
    passwordGroup.appendChild(passwordLabel);
    passwordGroup.appendChild(passwordInput);
    
    // Create submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.className = 'btn btn-primary';
    submitBtn.textContent = type === 'login' ? 'Log In' : 'Sign Up';
    
    // Add additional fields for signup
    if (type === 'signup') {
        // Create confirm password field
        const confirmPasswordGroup = document.createElement('div');
        confirmPasswordGroup.className = 'form-group';
        
        const confirmPasswordLabel = document.createElement('label');
        confirmPasswordLabel.textContent = 'Confirm Password';
        confirmPasswordLabel.setAttribute('for', 'confirm-password');
        
        const confirmPasswordInput = document.createElement('input');
        confirmPasswordInput.type = 'password';
        confirmPasswordInput.id = 'confirm-password';
        confirmPasswordInput.placeholder = 'Confirm your password';
        confirmPasswordInput.required = true;
        
        confirmPasswordGroup.appendChild(confirmPasswordLabel);
        confirmPasswordGroup.appendChild(confirmPasswordInput);
        
        // Insert confirm password before submit button
        form.appendChild(emailGroup);
        form.appendChild(passwordGroup);
        form.appendChild(confirmPasswordGroup);
    } else {
        form.appendChild(emailGroup);
        form.appendChild(passwordGroup);
    }
    
    // Add form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form values
        const email = emailInput.value;
        const password = passwordInput.value;
        
        // Simple validation
        if (!email || !password) {
            alert('Please fill in all fields');
            return;
        }
        
        // Disable form elements during authentication
        const formElements = form.querySelectorAll('input, button');
        formElements.forEach(el => el.disabled = true);
        
        // Show loading message
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'auth-loading';
        loadingMessage.textContent = type === 'login' 
            ? 'Logging in...' 
            : 'Creating your account...';
        form.appendChild(loadingMessage);
        
        try {
            if (type === 'signup') {
                const confirmPassword = document.getElementById('confirm-password').value;
                if (password !== confirmPassword) {
                    throw new Error('Passwords do not match');
                }
                
                // Additional fields for signup
                const name = email.split('@')[0]; // Simple name extraction from email
                
                // Register the user
                await AuthSession.signup({
                    email,
                    password,
                    name
                });
            } else {
                // Login the user
                await AuthSession.login(email, password);
            }
            
            // Show success message
            loadingMessage.className = 'auth-success';
            loadingMessage.textContent = type === 'login' 
                ? 'Login successful! Redirecting...' 
                : 'Account created successfully! Redirecting...';
            
            // Update UI to show authenticated state
            updateAuthUI(true);
            
            // Close modal after a short delay
            setTimeout(() => {
                modal.remove();
                // Redirect to dashboard
                window.location.href = 'dashboard.html';
            }, 1500);
            
        } catch (error) {
            // Show error message
            loadingMessage.className = 'auth-error';
            loadingMessage.textContent = error.message || 'Authentication failed';
            
            // Re-enable form elements
            formElements.forEach(el => el.disabled = false);
        }
    });
    
    // Add submit button to form
    form.appendChild(submitBtn);
    
    // Add alternative action link
    const altActionText = document.createElement('p');
    altActionText.className = 'auth-alt-action';
    
    if (type === 'login') {
        altActionText.innerHTML = 'Don\'t have an account? <a href="#" class="switch-auth">Sign up</a>';
    } else {
        altActionText.innerHTML = 'Already have an account? <a href="#" class="switch-auth">Log in</a>';
    }
    
    // Add event listener to switch between login and signup
    altActionText.querySelector('.switch-auth').addEventListener('click', function(e) {
        e.preventDefault();
        showAuthModal(type === 'login' ? 'signup' : 'login');
    });
    
    // Assemble modal
    modalContent.appendChild(closeBtn);
    modalContent.appendChild(title);
    modalContent.appendChild(form);
    modalContent.appendChild(altActionText);
    modal.appendChild(modalContent);
    
    // Add modal to body
    document.body.appendChild(modal);
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .auth-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .auth-modal-content {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            width: 100%;
            max-width: 400px;
            position: relative;
        }
        
        .auth-modal-close {
            position: absolute;
            top: 10px;
            right: 15px;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }
        
        .auth-form {
            margin-top: 20px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        
        .auth-alt-action {
            margin-top: 20px;
            text-align: center;
        }
        
        .auth-success {
            margin-top: 15px;
            padding: 10px;
            background-color: #d4edda;
            color: #155724;
            border-radius: 4px;
            text-align: center;
        }
        
        .auth-loading {
            margin-top: 15px;
            padding: 10px;
            background-color: #cce5ff;
            color: #004085;
            border-radius: 4px;
            text-align: center;
        }
        
        .auth-error {
            margin-top: 15px;
            padding: 10px;
            background-color: #f8d7da;
            color: #721c24;
            border-radius: 4px;
            text-align: center;
        }
        
        .user-menu {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .user-name {
            font-weight: 500;
            color: #333;
        }
        
        .logout-btn {
            padding: 8px 16px;
            border: 1px solid #dc3545;
            color: #dc3545;
            background: transparent;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .logout-btn:hover {
            background-color: #dc3545;
            color: white;
        }
    `;
    
    document.head.appendChild(style);
    
    // Focus on email input
    emailInput.focus();
}
