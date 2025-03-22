// Function to update notification count
function updateNotificationCount() {
    fetch('/admin_notifications/count/')
        .then(response => response.json())
        .then(data => {
            const countBadge = document.getElementById('notificationCountBadge');
            if (countBadge) {
                countBadge.textContent = data.count;
                
                // Add visual indicator if there are unread notifications
                if (data.count > 0) {
                    countBadge.classList.add('has-notifications');
                    countBadge.style.display = 'flex'; // Show badge when there are notifications
                } else {
                    countBadge.classList.remove('has-notifications');
                    countBadge.style.display = 'none'; // Hide badge when there are no notifications
                }
            }
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

// Update notification count immediately on page load
document.addEventListener('DOMContentLoaded', function() {
    updateNotificationCount();
    
    // Set up interval to periodically check for new notifications
    setInterval(updateNotificationCount, 10000); // Check every 10 seconds
    
    document.documentElement.style.overflow = 'auto';
    document.body.style.overflow = 'auto';
}); 