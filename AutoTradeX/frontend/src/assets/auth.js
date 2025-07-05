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
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form values
        const email = emailInput.value;
        const password = passwordInput.value;
        
        // Simple validation
        if (!email || !password) {
            alert('Please fill in all fields');
            return;
        }
        
        if (type === 'signup') {
            const confirmPassword = document.getElementById('confirm-password').value;
            if (password !== confirmPassword) {
                alert('Passwords do not match');
                return;
            }
        }
        
        // Here you would typically make an API call to your backend
        console.log(`${type === 'login' ? 'Logging in' : 'Signing up'} with email: ${email}`);
        
        // Show success message
        const formElements = form.querySelectorAll('input, button');
        formElements.forEach(el => el.disabled = true);
        
        const successMessage = document.createElement('div');
        successMessage.className = 'auth-success';
        successMessage.textContent = type === 'login' 
            ? 'Login successful! Redirecting...' 
            : 'Account created successfully! Redirecting...';
        
        form.appendChild(successMessage);
        
        // Simulate redirect after 2 seconds
        setTimeout(() => {
            modal.remove();
            alert(`${type === 'login' ? 'Login' : 'Signup'} successful! This is a demo - in a real app, you would be redirected to the dashboard.`);
        }, 2000);
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
    `;
    
    document.head.appendChild(style);
    
    // Focus on email input
    emailInput.focus();
}
