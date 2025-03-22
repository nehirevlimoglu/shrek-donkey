document.addEventListener('DOMContentLoaded', function() {
    // Mark as read functionality
    setupMarkAsRead();
    
    // Clear all notifications functionality
    setupClearAll();
    
    // Filter notifications functionality
    setupFilters();
    
    // Setup infinite scroll
    setupInfiniteScroll();
    
    // Setup notification actions
    setupNotificationActions();
});

function setupMarkAsRead() {
    // Mark individual notification as read
    const markReadButtons = document.querySelectorAll('.mark-read-btn');
    if (markReadButtons.length) {
        markReadButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                const notificationId = this.dataset.notificationId;
                const notificationItem = document.getElementById(`notification-${notificationId}`);
                
                fetch(`/admin/mark-notification-read/${notificationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update UI
                        if (notificationItem) {
                            notificationItem.classList.remove('unread');
                            notificationItem.classList.add('read');
                            
                            // Update read status indicator
                            const statusIndicator = notificationItem.querySelector('.status-indicator');
                            if (statusIndicator) {
                                statusIndicator.classList.remove('unread');
                                statusIndicator.classList.add('read');
                            }
                            
                            // Update button text
                            this.textContent = 'Marked as read';
                            this.disabled = true;
                        }
                        
                        // Update notification count
                        updateNotificationCount();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        });
    }
    
    // Mark all as read button
    const markAllReadBtn = document.getElementById('markAllRead');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/admin/mark-all-notifications-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI for all notifications
                    const unreadNotifications = document.querySelectorAll('.notification-item.unread');
                    unreadNotifications.forEach(item => {
                        item.classList.remove('unread');
                        item.classList.add('read');
                        
                        // Update status indicator
                        const statusIndicator = item.querySelector('.status-indicator');
                        if (statusIndicator) {
                            statusIndicator.classList.remove('unread');
                            statusIndicator.classList.add('read');
                        }
                        
                        // Update mark read buttons
                        const markReadBtn = item.querySelector('.mark-read-btn');
                        if (markReadBtn) {
                            markReadBtn.textContent = 'Marked as read';
                            markReadBtn.disabled = true;
                        }
                    });
                    
                    // Update notification count
                    updateNotificationCount();
                    
                    // Show success message
                    showNotification('All notifications marked as read', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
}

function setupClearAll() {
    const clearAllBtn = document.getElementById('clearAllNotifications');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('Are you sure you want to delete all notifications? This action cannot be undone.')) {
                fetch('/admin/clear-all-notifications/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Clear notifications container
                        const notificationsContainer = document.querySelector('.notifications-list');
                        if (notificationsContainer) {
                            notificationsContainer.innerHTML = '<div class="no-notifications">No notifications to display</div>';
                        }
                        
                        // Update notification count
                        updateNotificationCount();
                        
                        // Show success message
                        showNotification('All notifications cleared', 'success');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
        });
    }
}

function setupFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    if (filterButtons.length) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                // Remove active class from all buttons
                filterButtons.forEach(b => b.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Get filter value
                const filter = this.dataset.filter;
                
                // Apply filter
                filterNotifications(filter);
            });
        });
    }
}

function filterNotifications(filter) {
    const notificationItems = document.querySelectorAll('.notification-item');
    
    notificationItems.forEach(item => {
        if (filter === 'all') {
            item.style.display = '';
        } else if (filter === 'unread' && item.classList.contains('unread')) {
            item.style.display = '';
        } else if (filter === 'read' && item.classList.contains('read')) {
            item.style.display = '';
        } else if (filter === item.dataset.type) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
    
    // Check if no notifications are visible
    const visibleNotifications = document.querySelectorAll('.notification-item[style="display: none;"]');
    const notificationsContainer = document.querySelector('.notifications-list');
    
    if (visibleNotifications.length === notificationItems.length && notificationsContainer) {
        const noNotificationsMsg = document.createElement('div');
        noNotificationsMsg.className = 'no-notifications';
        noNotificationsMsg.textContent = 'No notifications match the selected filter';
        notificationsContainer.appendChild(noNotificationsMsg);
    } else {
        const noNotificationsMsg = document.querySelector('.no-notifications');
        if (noNotificationsMsg) {
            noNotificationsMsg.remove();
        }
    }
}

function setupInfiniteScroll() {
    const notificationsContainer = document.querySelector('.notifications-container');
    let page = 1;
    let loading = false;
    
    if (notificationsContainer) {
        notificationsContainer.addEventListener('scroll', function() {
            const { scrollTop, scrollHeight, clientHeight } = notificationsContainer;
            
            // Check if scrolled to bottom (with a threshold of 100px)
            if (scrollHeight - scrollTop - clientHeight < 100 && !loading) {
                loading = true;
                page++;
                
                // Get active filter
                const activeFilter = document.querySelector('.filter-btn.active');
                const filter = activeFilter ? activeFilter.dataset.filter : 'all';
                
                // Load more notifications
                fetch(`/admin/get-more-notifications/?page=${page}&filter=${filter}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.notifications && data.notifications.length > 0) {
                            // Append new notifications
                            appendNotifications(data.notifications);
                            
                            // Reattach event listeners
                            setupMarkAsRead();
                            setupNotificationActions();
                        }
                        
                        loading = false;
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        loading = false;
                    });
            }
        });
    }
}

function appendNotifications(notifications) {
    const notificationsList = document.querySelector('.notifications-list');
    if (!notificationsList) return;
    
    notifications.forEach(notification => {
        const notificationItem = document.createElement('div');
        notificationItem.className = `notification-item ${notification.read ? 'read' : 'unread'}`;
        notificationItem.id = `notification-${notification.id}`;
        notificationItem.dataset.type = notification.type;
        
        notificationItem.innerHTML = `
            <div class="notification-header">
                <span class="status-indicator ${notification.read ? 'read' : 'unread'}"></span>
                <h3 class="notification-title">${notification.title}</h3>
                <span class="notification-time">${notification.time}</span>
            </div>
            <div class="notification-content">
                <p>${notification.content}</p>
            </div>
            <div class="notification-actions">
                ${notification.read ? 
                    '<button class="mark-read-btn" data-notification-id="' + notification.id + '" disabled>Marked as read</button>' : 
                    '<button class="mark-read-btn" data-notification-id="' + notification.id + '">Mark as read</button>'}
                ${notification.actions ? renderActions(notification.actions, notification.id) : ''}
                <button class="delete-btn" data-notification-id="${notification.id}">Delete</button>
            </div>
        `;
        
        notificationsList.appendChild(notificationItem);
    });
}

function renderActions(actions, notificationId) {
    let actionsHtml = '';
    
    if (actions.view) {
        actionsHtml += `<a href="${actions.view}" class="action-btn view-btn">View</a>`;
    }
    
    if (actions.approve) {
        actionsHtml += `<button class="action-btn approve-btn" data-notification-id="${notificationId}" data-action="approve">Approve</button>`;
    }
    
    if (actions.reject) {
        actionsHtml += `<button class="action-btn reject-btn" data-notification-id="${notificationId}" data-action="reject">Reject</button>`;
    }
    
    return actionsHtml;
}

function setupNotificationActions() {
    // Delete notification buttons
    const deleteButtons = document.querySelectorAll('.delete-btn');
    if (deleteButtons.length) {
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const notificationId = this.dataset.notificationId;
                const notificationItem = document.getElementById(`notification-${notificationId}`);
                
                fetch(`/admin/delete-notification/${notificationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success && notificationItem) {
                        // Remove notification from UI with animation
                        notificationItem.style.opacity = '0';
                        setTimeout(() => {
                            notificationItem.remove();
                            
                            // Check if no notifications left
                            const remainingNotifications = document.querySelectorAll('.notification-item');
                            if (remainingNotifications.length === 0) {
                                const notificationsContainer = document.querySelector('.notifications-list');
                                if (notificationsContainer) {
                                    notificationsContainer.innerHTML = '<div class="no-notifications">No notifications to display</div>';
                                }
                            }
                        }, 300);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        });
    }
    
    // Approve and reject buttons
    const actionButtons = document.querySelectorAll('.approve-btn, .reject-btn');
    if (actionButtons.length) {
        actionButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const notificationId = this.dataset.notificationId;
                const action = this.dataset.action;
                
                fetch(`/admin/notification-action/${notificationId}/${action}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Disable all action buttons for this notification
                        const notificationItem = document.getElementById(`notification-${notificationId}`);
                        if (notificationItem) {
                            const actionBtns = notificationItem.querySelectorAll('.approve-btn, .reject-btn');
                            actionBtns.forEach(actionBtn => {
                                actionBtn.disabled = true;
                            });
                            
                            // Update button text
                            this.textContent = action === 'approve' ? 'Approved' : 'Rejected';
                            
                            // Mark as read
                            notificationItem.classList.remove('unread');
                            notificationItem.classList.add('read');
                            
                            // Update status indicator
                            const statusIndicator = notificationItem.querySelector('.status-indicator');
                            if (statusIndicator) {
                                statusIndicator.classList.remove('unread');
                                statusIndicator.classList.add('read');
                            }
                            
                            // Show success message
                            showNotification(`Action ${action} completed successfully`, 'success');
                        }
                    } else {
                        showNotification(`Error: ${data.error || 'Something went wrong'}`, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification('An error occurred while processing your request', 'error');
                });
            });
        });
    }
}

function updateNotificationCount() {
    fetch('/admin/notification-count/')
        .then(response => response.json())
        .then(data => {
            // Update count in the header
            const countBadge = document.getElementById('notificationCountBadge');
            if (countBadge) {
                countBadge.textContent = data.count;
                
                if (data.count > 0) {
                    countBadge.classList.add('has-notifications');
                    countBadge.style.display = 'flex';
                } else {
                    countBadge.classList.remove('has-notifications');
                    countBadge.style.display = 'none';
                }
            }
            
            // Update count in the notifications page header
            const pageCountElement = document.getElementById('notificationPageCount');
            if (pageCountElement) {
                pageCountElement.textContent = data.count;
            }
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast-notification ${type}`;
    notification.textContent = message;
    
    // Append to body
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Helper function to get CSRF token
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

// Function to update global notification count in header
function updateGlobalNotificationCount() {
    // Call the same API endpoint that updates the header count
    fetch('/admin_notifications/count/')
        .then(response => response.json())
        .then(data => {
            const countBadge = document.getElementById('notificationCountBadge');
            if (countBadge) {
                countBadge.textContent = data.count;
                
                if (data.count > 0) {
                    countBadge.classList.add('has-notifications');
                    countBadge.style.display = 'flex';
                } else {
                    countBadge.classList.remove('has-notifications');
                    countBadge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error updating notification count:', error));
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    // Filter form auto-submit on select change
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    });
    
    // Mark notification as read
    const markReadBtns = document.querySelectorAll('.mark-read-btn');
    markReadBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const notificationId = this.getAttribute('data-id');
            
            fetch(`/admin_notifications/mark_read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update UI
                    const card = document.querySelector(`.notification-card[data-id="${notificationId}"]`);
                    card.classList.remove('unread');
                    this.remove();
                    
                    // Update notification count
                    updateGlobalNotificationCount();
                    
                    // Update stats on page
                    const unreadCountEl = document.querySelector('.stats-item:nth-child(2) strong');
                    if (unreadCountEl) {
                        const currentCount = parseInt(unreadCountEl.textContent);
                        if (currentCount > 0) {
                            unreadCountEl.textContent = currentCount - 1;
                        }
                    }
                }
            })
            .catch(error => console.error('Error marking notification as read:', error));
        });
    });
    
    // Delete notification
    const deleteBtns = document.querySelectorAll('.delete-btn');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const notificationId = this.getAttribute('data-id');
            
            if (confirm('Are you sure you want to delete this notification?')) {
                fetch(`/admin_notifications/delete/${notificationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Remove notification from DOM
                        const card = document.querySelector(`.notification-card[data-id="${notificationId}"]`);
                        card.remove();
                        
                        // Update stats
                        const totalCountEl = document.querySelector('.stats-item:first-child strong');
                        totalCountEl.textContent = parseInt(totalCountEl.textContent) - 1;
                        
                        // Check if card was unread
                        if (card.classList.contains('unread')) {
                            const unreadCountEl = document.querySelector('.stats-item:nth-child(2) strong');
                            if (unreadCountEl) {
                                unreadCountEl.textContent = parseInt(unreadCountEl.textContent) - 1;
                                
                                // Update notification count
                                updateGlobalNotificationCount();
                            }
                        }
                        
                        // Show "no notifications" message if all notifications are deleted
                        if (document.querySelectorAll('.notification-card').length === 0) {
                            const noNotifications = document.createElement('p');
                            noNotifications.className = 'no-notifications';
                            noNotifications.textContent = 'No notifications available';
                            document.querySelector('.notifications-list').appendChild(noNotifications);
                        }
                    }
                })
                .catch(error => console.error('Error deleting notification:', error));
            }
        });
    });
    
    // Mark all notifications as read
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to mark all notifications as read?')) {
                fetch('/admin_notifications/mark_all_read/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Update UI
                        document.querySelectorAll('.notification-card.unread').forEach(card => {
                            card.classList.remove('unread');
                            card.querySelector('.mark-read-btn')?.remove();
                        });
                        
                        // Update notification count
                        document.querySelector('.stats-item:nth-child(2) strong').textContent = '0';
                        updateGlobalNotificationCount();
                        
                        // Hide the button
                        this.style.display = 'none';
                    }
                })
                .catch(error => console.error('Error marking all notifications as read:', error));
            }
        });
    }
    
    // Delete all notifications
    const deleteAllBtn = document.getElementById('deleteAllBtn');
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete all notifications? This action cannot be undone.')) {
                fetch('/admin_notifications/delete_all/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Update UI
                        document.querySelectorAll('.notification-card').forEach(card => {
                            card.remove();
                        });
                        
                        // Update stats
                        document.querySelector('.stats-item:first-child strong').textContent = '0';
                        document.querySelector('.stats-item:nth-child(2) strong').textContent = '0';
                        document.querySelector('.stats-item:nth-child(3) strong').textContent = '0';
                        
                        // Update notification count
                        updateGlobalNotificationCount();
                        
                        // Show "no notifications" message
                        const noNotifications = document.createElement('p');
                        noNotifications.className = 'no-notifications';
                        noNotifications.textContent = 'No notifications available';
                        document.querySelector('.notifications-list').appendChild(noNotifications);
                        
                        // Hide the mark all read button
                        const markAllReadBtn = document.getElementById('markAllReadBtn');
                        if (markAllReadBtn) {
                            markAllReadBtn.style.display = 'none';
                        }
                    }
                })
                .catch(error => console.error('Error deleting all notifications:', error));
            }
        });
    }
    
    // Feedback specific functionality
    // Mark feedback as resolved
    const resolveBtns = document.querySelectorAll('.resolve-btn');
    resolveBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const notificationId = this.getAttribute('data-id');
            const feedbackId = this.getAttribute('data-feedback-id');
            
            fetch(`/admin_feedback/resolve/${feedbackId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update UI
                    const card = document.querySelector(`.notification-card[data-id="${notificationId}"]`);
                    const resolveBtn = card.querySelector('.resolve-btn');
                    
                    // Change button text and disable it
                    resolveBtn.textContent = 'Resolved';
                    resolveBtn.disabled = true;
                    resolveBtn.style.backgroundColor = '#9ca3af';
                    
                    // Update feedback count if needed
                    const feedbackCountEl = document.querySelector('.stats-item:nth-child(3) strong');
                    if (feedbackCountEl) {
                        const currentCount = parseInt(feedbackCountEl.textContent);
                        if (!isNaN(currentCount)) {
                            feedbackCountEl.textContent = currentCount - 1;
                        }
                    }
                    
                    // Update global notification count
                    updateGlobalNotificationCount();
                    
                    // Show success message
                    const message = document.createElement('div');
                    message.className = 'alert alert-success mt-2';
                    message.style.fontSize = '0.8rem';
                    message.textContent = 'Feedback marked as resolved';
                    card.querySelector('.feedback-actions').appendChild(message);
                    
                    // Remove message after 3 seconds
                    setTimeout(() => {
                        message.remove();
                    }, 3000);
                }
            })
            .catch(error => console.error('Error resolving feedback:', error));
        });
    });
    
    // Contact user via email
    const contactBtns = document.querySelectorAll('.contact-btn');
    contactBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const email = this.getAttribute('data-email');
            const subject = encodeURIComponent('Response to your feedback - Swamp Hiring');
            
            // Open email client with pre-filled information
            window.location.href = `mailto:${email}?subject=${subject}`;
        });
    });
}); 