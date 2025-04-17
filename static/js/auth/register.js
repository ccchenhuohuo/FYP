document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    
    if (registerForm) {
        // Clear any initial error states on the form
        clearErrors();
        
        registerForm.addEventListener('submit', function(e) {
            // Clear previous errors
            clearErrors();
            
            const userName = document.getElementById('user_name').value.trim();
            const userEmail = document.getElementById('user_email').value.trim();
            const userPassword = document.getElementById('user_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            let isValid = true;
            
            // Validate username
            if (!userName) {
                isValid = false;
                showError('user_name', 'Please enter a username');
            }
            
            // Validate email
            if (!userEmail) {
                isValid = false;
                showError('user_email', 'Please enter an email address');
            } else {
                // Validate email format
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(userEmail)) {
                    isValid = false;
                    showError('user_email', 'Please enter a valid email address');
                }
            }
            
            // Validate password
            if (!userPassword) {
                isValid = false;
                showError('user_password', 'Please enter a password');
            }
            
            // Validate confirm password
            if (!confirmPassword) {
                isValid = false;
                showError('confirm_password', 'Please confirm your password');
            } else if (userPassword !== confirmPassword) {
                isValid = false;
                showError('confirm_password', 'Passwords do not match');
            }
            
            if (!isValid) {
                e.preventDefault(); // Prevent form submission
            }
        });
    }
    
    // Helper function: Show error message
    function showError(inputId, message) {
        const input = document.getElementById(inputId);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        // Insert error message after the input field
        input.parentNode.insertBefore(errorDiv, input.nextSibling);
        input.classList.add('error');
    }
    
    // Helper function: Clear all errors
    function clearErrors() {
        // Remove all error messages
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(msg => msg.remove());
        
        // Remove all error styles
        const errorInputs = document.querySelectorAll('.error');
        errorInputs.forEach(input => input.classList.remove('error'));
    }
}); 