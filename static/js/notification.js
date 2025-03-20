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
                } else {
                    countBadge.classList.remove('has-notifications');
                }
            }
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

// Update notification count every 30 seconds
setInterval(updateNotificationCount, 30000);

// Initial update on page load
document.addEventListener('DOMContentLoaded', function() {
    updateNotificationCount();
});
