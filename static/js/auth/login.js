document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // Validation before form submission
            const username = document.getElementById('user_name').value.trim();
            const password = document.getElementById('user_password').value.trim();
            
            if (!username || !password) {
                e.preventDefault(); // Prevent form submission
                alert('Please enter username and password');
                return false;
            }
            
            // If validation passes, the form submits normally
            return true;
        });
    }
}); 