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
    
    // Handle notification preferences
    const notificationForm = document.querySelector('form[name="notification_preferences"]');
    if (notificationForm) {
        const dashboardDelivery = document.getElementById('dashboard_delivery');
        const emailDelivery = document.getElementById('email_delivery');
        
        // Ensure at least one delivery method is checked
        function validateDeliveryMethods() {
            if (!dashboardDelivery.checked && !emailDelivery.checked) {
                // If neither is checked, check dashboard by default
                dashboardDelivery.checked = true;
                
                // Show alert
                const alert = document.createElement('div');
                alert.className = 'alert alert-warning alert-dismissible fade show mt-3';
                alert.role = 'alert';
                alert.innerHTML = `
                    At least one notification delivery method must be enabled.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                notificationForm.prepend(alert);
                
                // Auto dismiss after 3 seconds
                setTimeout(() => {
                    alert.classList.remove('show');
                    setTimeout(() => alert.remove(), 150);
                }, 3000);
            }
        }
        
        // Add event listeners
        dashboardDelivery.addEventListener('change', validateDeliveryMethods);
        emailDelivery.addEventListener('change', validateDeliveryMethods);
        
        // Validate on form submission
        notificationForm.addEventListener('submit', function(e) {
            validateDeliveryMethods();
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