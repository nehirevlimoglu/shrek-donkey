document.addEventListener('DOMContentLoaded', function() {
    // Mark as read functionality
    setupMarkAsRead();
    
    // Clear all notifications functionality
    setupClearAll();
    
    // Filter notifications functionality
    setupFilters();
    
    // Setup infinite scroll
    setupInfiniteScroll();
    
    // Setup notification actions (delete, approve/reject, etc.)
    setupNotificationActions();
    
    // Setup candidate view buttons
    setupCandidateView();
    
    // Setup filter auto-submit on select change
    setupFilterAutoSubmit();
    
    // Update notification count immediately and set interval for auto refresh
    updateNotificationCount();
    updateNotificationStats(); // Update stats immediately
    setInterval(updateNotificationCount, 5000); // Check every 5 seconds for updates
    setInterval(updateNotificationStats, 10000); // Update statistics every 10 seconds
});

function setupMarkAsRead() {
    document.querySelectorAll('.mark-read-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.getAttribute('data-id');
            const notificationCard = document.getElementById(`notification-${notificationId}`);
            
            // Use fetch API instead of form submission
            fetch(`/admin_notifications/mark_read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update UI
                    if (notificationCard) {
                        notificationCard.classList.remove('unread');
                        
                        // Replace the mark-read button with mark-unread button
                        const markReadBtn = this;
                        const markUnreadBtn = document.createElement('button');
                        markUnreadBtn.className = 'mark-unread-btn';
                        markUnreadBtn.setAttribute('data-id', notificationId);
                        markUnreadBtn.title = 'Mark as Unread';
                        markUnreadBtn.innerHTML = '↻';
                        
                        if (markReadBtn.parentNode) {
                            markReadBtn.parentNode.replaceChild(markUnreadBtn, markReadBtn);
                            
                            // Add event listener to the new button
                            markUnreadBtn.addEventListener('click', handleMarkUnread);
                        }
                    }
                    
                    // Update notification count
                    updateNotificationCount();
                } else {
                    console.error('Error marking notification as read:', data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

    document.querySelectorAll('.mark-unread-btn').forEach(button => {
        button.addEventListener('click', handleMarkUnread);
    });
    
    // Function to handle mark as unread button clicks
    function handleMarkUnread(e) {
        e.preventDefault();
        const notificationId = this.getAttribute('data-id');
        const notificationCard = document.getElementById(`notification-${notificationId}`);
        
        // Use fetch API
        fetch(`/admin_notifications/mark_unread/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Update UI
                if (notificationCard) {
                    notificationCard.classList.add('unread');
                    
                    // Replace the mark-unread button with mark-read button
                    const markUnreadBtn = this;
                    const markReadBtn = document.createElement('button');
                    markReadBtn.className = 'mark-read-btn';
                    markReadBtn.setAttribute('data-id', notificationId);
                    markReadBtn.title = 'Mark as Read';
                    markReadBtn.innerHTML = '✓';
                    
                    if (markUnreadBtn.parentNode) {
                        markUnreadBtn.parentNode.replaceChild(markReadBtn, markUnreadBtn);
                        
                        // Add event listener to the new button
                        markReadBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            const id = this.getAttribute('data-id');
                            document.querySelector(`.mark-read-btn[data-id="${id}"]`).click();
                        });
                    }
                }
                
                // Update notification count
                updateNotificationCount();
            } else {
                console.error('Error marking notification as unread:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

function setupClearAll() {
    const clearAllBtn = document.getElementById('deleteAllBtn');
    const modal = document.getElementById('confirmClearModal');
    const confirmYesBtn = document.getElementById('confirmClearYes');
    const confirmNoBtn = document.getElementById('confirmClearNo');

    if (clearAllBtn && modal && confirmYesBtn && confirmNoBtn) {
        clearAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            modal.style.display = 'block'; // Show the clear all modal
        });

        confirmNoBtn.addEventListener('click', function() {
            modal.style.display = 'none'; // Hide the modal
        });

        confirmYesBtn.addEventListener('click', function() {
            modal.style.display = 'none'; // Hide modal while processing
            fetch('/clear-all-notifications/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
            
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const notificationsContainer = document.querySelector('.notifications-list');
                    if (notificationsContainer) {
                        notificationsContainer.innerHTML = '<div class="no-notifications">No notifications to display</div>';
                        console.log(`Cleared ${data.count || 'all'} notifications`);
                    }
                    // Update notification count
                    updateNotificationCount();
                    // Show success message
                    showNotification(`All notifications cleared (${data.count || 'all'})`, 'success');
                    
                    // Force immediate update of stats
                    updateNotificationStats();
                } else {
                    console.error('Error clearing notifications:', data.error || 'Unknown error');
                    showNotification(data.error || 'Error clearing notifications', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
}

function setupFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    if (filterButtons.length) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                filterButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                const filter = this.dataset.filter;
                filterNotifications(filter);
            });
        });
    }
}

function filterNotifications(filter) {
    const notificationItems = document.querySelectorAll('.notification-card');
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
    const visibleNotifications = Array.from(notificationItems).filter(item => item.style.display !== 'none');
    const notificationsContainer = document.querySelector('.notifications-list');
    if (visibleNotifications.length === 0 && notificationsContainer) {
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
            if (scrollHeight - scrollTop - clientHeight < 100 && !loading) {
                loading = true;
                page++;
                const activeFilter = document.querySelector('.filter-btn.active');
                const filter = activeFilter ? activeFilter.dataset.filter : 'all';
                fetch(`/admin/get-more-notifications/?page=${page}&filter=${filter}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.notifications && data.notifications.length > 0) {
                            appendNotifications(data.notifications);
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
                    '<button class="mark-unread-btn" data-id="' + notification.id + '" title="Mark as Unread">↻</button>' : 
                    '<button class="mark-read-btn" data-id="' + notification.id + '">Mark as Read</button>'}
                ${notification.actions ? renderActions(notification.actions, notification.id) : ''}
                <button class="delete-btn" data-id="${notification.id}">Delete</button>
            </div>
        `;
        notificationsList.appendChild(notificationItem);
    });
    
    // Add event listeners to new buttons
    const newMarkReadButtons = notificationsList.querySelectorAll('.mark-read-btn');
    if (newMarkReadButtons.length) {
        newMarkReadButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const notificationId = this.dataset.id;
                const notificationItem = document.getElementById(`notification-${notificationId}`);
                
                fetch(`/admin_notifications/mark_read/${notificationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status == 'success') {
                        if (notificationItem) {
                            notificationItem.classList.remove('unread');
                            notificationItem.classList.add('read');
                            
                            const statusIndicator = notificationItem.querySelector('.status-indicator');
                            if (statusIndicator) {
                                statusIndicator.classList.remove('unread');
                                statusIndicator.classList.add('read');
                            }
                            
                            // Replace button
                            const markUnreadBtn = document.createElement('button');
                            markUnreadBtn.className = 'mark-unread-btn';
                            markUnreadBtn.dataset.id = notificationId;
                            markUnreadBtn.title = 'Mark as Unread';
                            markUnreadBtn.innerHTML = '↻';
                            this.parentNode.replaceChild(markUnreadBtn, this);
                            
                            // Add event listener
                            markUnreadBtn.addEventListener('click', handleMarkUnread);
                        }
                        
                        updateNotificationCount();
                        updateNotificationStats();
                    }
                });
            });
        });
    }
    
    const newMarkUnreadButtons = notificationsList.querySelectorAll('.mark-unread-btn');
    if (newMarkUnreadButtons.length) {
        newMarkUnreadButtons.forEach(btn => {
            btn.addEventListener('click', handleMarkUnread);
        });
    }
}

function renderActions(actions, notificationId) {
    let actionsHtml = '';
    if (actions.view) {
        actionsHtml += `<a href="${actions.view}" class="action-btn view-btn">View</a>`;
    }
    if (actions.approve) {
        actionsHtml += `<button class="action-btn approve-btn" data-id="${notificationId}" data-action="approve">Approve</button>`;
    }
    if (actions.reject) {
        actionsHtml += `<button class="action-btn reject-btn" data-id="${notificationId}" data-action="reject">Reject</button>`;
    }
    return actionsHtml;
}

function setupNotificationActions() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    if (deleteButtons.length) {
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const notificationId = this.dataset.id;
                const notificationItem = document.getElementById(`notification-${notificationId}`);
                showConfirmationModal({
                    title: 'Delete Notification?',
                    message: 'Are you sure you want to delete this notification?',
                    onConfirm: () => {
                        fetch(`/admin_notifications/delete/${notificationId}/`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': getCsrfToken(),
                                'Content-Type': 'application/json'
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success' && notificationItem) {
                                // Apply fade-out effect
                                notificationItem.style.opacity = '0';
                                setTimeout(() => {
                                    // Remove the element
                                    notificationItem.remove();
                                    
                                    // Check if there are any remaining notifications
                                    const remaining = document.querySelectorAll('.notification-card');
                                    console.log(`Remaining notifications: ${remaining.length}`);
                                    
                                    if (remaining.length === 0) {
                                        const container = document.querySelector('.notifications-list');
                                        if (container) {
                                            container.innerHTML = '<div class="no-notifications">No notifications to display</div>';
                                        }
                                    }
                                    
                                    // Update notification count
                                    updateNotificationCount();
                                    // Show success message
                                    showNotification('Notification deleted', 'success');

                                    // Force immediate update of stats
                                    updateNotificationStats();
                                }, 300);
                            } else {
                                // Show error message
                                console.error('Error deleting notification:', data.message || 'Unknown error');
                                showNotification(data.message || 'Error deleting notification', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                    }
                });
            });
        });
    }
    
    const actionButtons = document.querySelectorAll('.approve-btn, .reject-btn');
    if (actionButtons.length) {
        actionButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const notificationId = this.dataset.id;
                const action = this.dataset.action;
                fetch(`/admin_notifications/action/${notificationId}/${action}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const notificationItem = document.getElementById(`notification-${notificationId}`);
                        if (notificationItem) {
                            const actionBtns = notificationItem.querySelectorAll('.approve-btn, .reject-btn');
                            actionBtns.forEach(btn => btn.disabled = true);
                            this.textContent = action === 'approve' ? 'Approved' : 'Rejected';
                            notificationItem.classList.remove('unread');
                            notificationItem.classList.add('read');
                            const statusIndicator = notificationItem.querySelector('.status-indicator');
                            if (statusIndicator) {
                                statusIndicator.classList.remove('unread');
                                statusIndicator.classList.add('read');
                            }
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
            
            // Update count display on the notifications page if present
            const pageCountElement = document.getElementById('notificationPageCount');
            if (pageCountElement) {
                pageCountElement.textContent = data.count;
            }
            
            // Update the unread count in the sidebar if present
            const sidebarUnreadCount = document.querySelector('.unread-count');
            if (sidebarUnreadCount) {
                sidebarUnreadCount.textContent = data.count;
                if (data.count === 0) {
                    sidebarUnreadCount.style.display = 'none';
                } else {
                    sidebarUnreadCount.style.display = 'inline-block';
                }
            }
            
            // Update statistics counts in the stats-item elements
            updateNotificationStats();
            
            console.log('Notification count updated:', data.count);
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `toast-notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function setupFilterAutoSubmit() {
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    });
}

function setupCandidateView() {
    const viewCandidateBtns = document.querySelectorAll('.view-candidate-btn');
    viewCandidateBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const candidateId = this.dataset.candidateId;
            fetch(`/admin_get-candidate-info/${candidateId}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Server responded with status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    displayCandidateModal(data);
                })
                .catch(error => {
                    console.error('Error fetching candidate info:', error);
                    showConfirmationModal({
                        title: 'Error',
                        message: 'An error occurred while fetching candidate information.'
                    });
                });
        });
    });
}

function displayCandidateModal(candidateData) {
    let modal = document.getElementById('candidateModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'candidateModal';
        modal.className = 'modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        const closeBtn = document.createElement('span');
        closeBtn.className = 'close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => { modal.style.display = 'none'; };
        
        const candidateInfo = document.createElement('div');
        candidateInfo.id = 'candidateInfo';
        candidateInfo.className = 'candidate-info';
        
        modalContent.appendChild(closeBtn);
        modalContent.appendChild(candidateInfo);
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    const candidateInfo = document.getElementById('candidateInfo');
    candidateInfo.innerHTML = `
        <h2>${candidateData.name || 'Candidate'}</h2>
        <div class="info-item"><strong>Email:</strong> ${candidateData.email || 'Not provided'}</div>
        <div class="info-item"><strong>Applied On:</strong> ${candidateData.application_date || 'Unknown'}</div>
        <div class="info-item"><strong>Status:</strong> ${candidateData.status || 'Pending'}</div>
        <div class="status-update">
            <h3>Update Application Status</h3>
            <select id="applicationStatus">
                <option value="Pending" ${candidateData.status === 'Pending' ? 'selected' : ''}>Pending</option>
                <option value="Interview" ${candidateData.status === 'Interview' ? 'selected' : ''}>Interview Scheduled</option>
                <option value="Hired" ${candidateData.status === 'Hired' ? 'selected' : ''}>Hired</option>
                <option value="Rejected" ${candidateData.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
            </select>
            <button class="update-btn" data-candidate-id="${candidateData.id}">Update Status</button>
        </div>
    `;
    
    const updateBtn = candidateInfo.querySelector('.update-btn');
    updateBtn.addEventListener('click', function() {
        const candidateId = this.dataset.candidateId;
        const newStatus = document.getElementById('applicationStatus').value;
        
        fetch(`/admin_update-candidate-status/${candidateId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                modal.style.display = 'none';
                window.location.reload();
            } else {
                showConfirmationModal({
                    title: 'Error Updating Status',
                    message: data.error || 'Unknown error'
                });
            }
        })
        .catch(error => {
            console.error('Error updating candidate status:', error);
            showConfirmationModal({
                title: 'Error',
                message: 'An error occurred while updating the candidate status.'
            });
        });
    });
    
    modal.style.display = 'block';
}

function getCsrfToken() {
    // Method 1: Get from cookie
    let cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    // Method 2: Get from meta tag
    if (!cookieValue) {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            cookieValue = metaTag.getAttribute('content');
        }
    }
    
    // Method 3: Get from form
    if (!cookieValue) {
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            cookieValue = csrfInput.value;
        }
    }
    
    if (!cookieValue) {
        console.error("Unable to get CSRF token, this may cause request failures");
    }
    
    return cookieValue;
}

// Custom confirmation modal function
function showConfirmationModal(options) {
    let confirmModal = document.getElementById('confirmModal');
    if (!confirmModal) {
        // Create the modal element
        confirmModal = document.createElement('div');
        confirmModal.id = 'confirmModal';
        confirmModal.className = 'modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        const closeBtn = document.createElement('span');
        closeBtn.className = 'close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => { confirmModal.style.display = 'none'; };
        
        const titleElem = document.createElement('h2');
        titleElem.id = 'confirmModalTitle';
        
        const messageElem = document.createElement('p');
        messageElem.id = 'confirmModalMessage';
        
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'confirm-actions';
        
        const yesBtn = document.createElement('button');
        yesBtn.id = 'confirmModalYes';
        yesBtn.className = 'update-btn';
        yesBtn.textContent = 'Confirm';
        
        const noBtn = document.createElement('button');
        noBtn.id = 'confirmModalNo';
        noBtn.className = 'update-btn';
        noBtn.textContent = 'Cancel';
        
        actionsDiv.appendChild(yesBtn);
        actionsDiv.appendChild(noBtn);
        
        modalContent.appendChild(closeBtn);
        modalContent.appendChild(titleElem);
        modalContent.appendChild(messageElem);
        modalContent.appendChild(actionsDiv);
        
        confirmModal.appendChild(modalContent);
        document.body.appendChild(confirmModal);
        
        window.addEventListener('click', function(event) {
            if (event.target === confirmModal) {
                confirmModal.style.display = 'none';
            }
        });
    }
    
    document.getElementById('confirmModalTitle').textContent = options.title || 'Confirm';
    document.getElementById('confirmModalMessage').textContent = options.message || 'Are you sure?';
    
    confirmModal.style.display = 'block';
    
    document.getElementById('confirmModalYes').onclick = function() {
        confirmModal.style.display = 'none';
        if (options.onConfirm && typeof options.onConfirm === 'function') {
            options.onConfirm();
        }
    };
    
    document.getElementById('confirmModalNo').onclick = function() {
        confirmModal.style.display = 'none';
        if (options.onCancel && typeof options.onCancel === 'function') {
            options.onCancel();
        }
    };
}

// Add a new function to update just the statistics
function updateNotificationStats() {
    const statsItems = document.querySelectorAll('.stats-item strong');
    if (statsItems.length > 0) {
        // Get updated stats from server
        fetch('/admin_notifications/stats/')
            .then(response => response.json())
            .then(stats => {
                // Update total count
                if (statsItems[0]) statsItems[0].textContent = stats.total_count || '0';
                // Update unread count
                if (statsItems[1]) statsItems[1].textContent = stats.unread_count || '0';
                // Update other stats if available
                if (statsItems[2] && stats.feedback_count !== undefined) {
                    statsItems[2].textContent = stats.feedback_count || '0';
                }
                
                // Update type counts in filter options
                if (stats.type_counts) {
                    Object.keys(stats.type_counts).forEach(type => {
                        const typeOption = document.querySelector(`option[value="${type}"]`);
                        if (typeOption) {
                            const optionText = typeOption.textContent.split('(')[0].trim();
                            typeOption.textContent = `${optionText} (${stats.type_counts[type]})`;
                        }
                    });
                }
                
                // Update priority counts in filter options
                if (stats.priority_counts) {
                    Object.keys(stats.priority_counts).forEach(priority => {
                        const priorityOption = document.querySelector(`option[value="${priority}"]`);
                        if (priorityOption) {
                            const optionText = priorityOption.textContent.split('(')[0].trim();
                            priorityOption.textContent = `${optionText} (${stats.priority_counts[priority]})`;
                        }
                    });
                }
                
                console.log('Statistics updated successfully');
            })
            .catch(error => console.error('Error fetching notification stats:', error));
    }
}
