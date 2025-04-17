document.addEventListener('DOMContentLoaded', function() {
    const adminLoginForm = document.getElementById('adminLoginForm');
    
    // Handle account lock countdown
    const lockCountdownElement = document.getElementById('lockCountdown');
    if (lockCountdownElement) {
        const lockedUntilElement = document.querySelector('.account-locked-info');
        if (lockedUntilElement) {
            const lockedUntilStr = lockedUntilElement.getAttribute('data-locked-until');
            if (lockedUntilStr) {
                const lockedUntil = new Date(lockedUntilStr);
                
                function updateCountdown() {
                    const now = new Date();
                    const diff = lockedUntil - now;
                    
                    if (diff <= 0) {
                        lockCountdownElement.textContent = "Unlocked, please refresh the page";
                        return;
                    }
                    
                    const minutes = Math.floor(diff / 60000);
                    const seconds = Math.floor((diff % 60000) / 1000);
                    lockCountdownElement.textContent = 
                        `${minutes}m ${seconds}s`; // Use m and s for minutes and seconds
                }
                
                // Initial update
                updateCountdown();
                // Update every second
                setInterval(updateCountdown, 1000);
            }
        }
    }
    
    // Show password complexity requirements (if element exists)
    const passwordField = document.getElementById('password');
    const passwordRequirements = document.getElementById('passwordRequirements');
    
    if (passwordField && passwordRequirements) {
        // Show requirements on focus
        passwordField.addEventListener('focus', function() {
            passwordRequirements.style.display = 'block';
        });
        
        // Hide requirements on blur (with a delay)
        passwordField.addEventListener('blur', function() {
            setTimeout(() => {
                passwordRequirements.style.display = 'none';
            }, 200);
        });
    }
    
    // Form submission validation
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                e.preventDefault();
                alert('Please enter admin username and password');
            }
        });
    }
});