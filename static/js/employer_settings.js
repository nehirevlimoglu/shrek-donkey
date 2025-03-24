document.addEventListener('DOMContentLoaded', function() {
    const tabLinks = document.querySelectorAll('.list-group-item-action');
    
    // Handle tab switching
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // The default link behavior (URL parameter) will handle the tab switching
            // This is just a hook for potential future enhancements
        });
    });
    
    // Password validation
    const passwordForm = document.querySelector('form[name="change_password"]');
    if (passwordForm) {
        const newPasswordInput = document.getElementById('new_password');
        const confirmPasswordInput = document.getElementById('confirm_password');
        const submitButton = passwordForm.querySelector('button[type="submit"]');
        
        // Function to validate password
        function validatePassword() {
            const newPassword = newPasswordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            // Check password length
            if (newPassword.length < 8) {
                newPasswordInput.classList.add('is-invalid');
                newPasswordInput.setCustomValidity('Password must be at least 8 characters long');
            } else {
                newPasswordInput.classList.remove('is-invalid');
                newPasswordInput.setCustomValidity('');
            }
            
            // Check if passwords match
            if (newPassword !== confirmPassword && confirmPassword.length > 0) {
                confirmPasswordInput.classList.add('is-invalid');
                confirmPasswordInput.setCustomValidity('Passwords do not match');
            } else {
                confirmPasswordInput.classList.remove('is-invalid');
                confirmPasswordInput.setCustomValidity('');
            }
        }
        
        // Add event listeners for password validation
        newPasswordInput.addEventListener('input', validatePassword);
        confirmPasswordInput.addEventListener('input', validatePassword);
        
        // Form submission validation
        passwordForm.addEventListener('submit', function(e) {
            validatePassword();
            
            if (!passwordForm.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            passwordForm.classList.add('was-validated');
        });
    }
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) closeButton.click();
        }, 5000);
    });
}); 