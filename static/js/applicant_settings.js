document.addEventListener('DOMContentLoaded', function() {
    // Tab switching event listeners (placeholder for potential future enhancements)
    const tabLinks = document.querySelectorAll('.list-group-item-action');
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // URL parameters handle the tab switching.
        });
    });

    // Password validation
    const passwordForm = document.querySelector('form[name="change_password"]');
    if (passwordForm) {
        const newPasswordInput = document.getElementById('new_password');
        const confirmPasswordInput = document.getElementById('confirm_password');
        
        function validatePassword() {
            const newPassword = newPasswordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            // Validate password length
            if (newPassword.length < 8) {
                newPasswordInput.classList.add('is-invalid');
                newPasswordInput.setCustomValidity('Password must be at least 8 characters long');
            } else {
                newPasswordInput.classList.remove('is-invalid');
                newPasswordInput.setCustomValidity('');
            }
            
            // Validate matching passwords
            if (newPassword !== confirmPassword && confirmPassword.length > 0) {
                confirmPasswordInput.classList.add('is-invalid');
                confirmPasswordInput.setCustomValidity('Passwords do not match');
            } else {
                confirmPasswordInput.classList.remove('is-invalid');
                confirmPasswordInput.setCustomValidity('');
            }
        }
        
        newPasswordInput.addEventListener('input', validatePassword);
        confirmPasswordInput.addEventListener('input', validatePassword);
        
        passwordForm.addEventListener('submit', function(e) {
            validatePassword();
            if (!passwordForm.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            passwordForm.classList.add('was-validated');
        });
    }

    // Auto-dismiss alerts after 5 seconds (except danger alerts)
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) closeButton.click();
        }, 5000);
    });
});
