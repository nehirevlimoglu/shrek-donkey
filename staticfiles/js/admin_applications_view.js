document.addEventListener('DOMContentLoaded', function() {
    // Setup filter functionality
    setupFilters();
    
    // Setup search functionality
    setupSearch();
    
    // Setup pagination
    setupPagination();
    
    // Setup application status updates
    setupStatusUpdates();
});

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
                
                // Update URL with filter parameter
                const url = new URL(window.location);
                url.searchParams.set('filter', filter);
                window.history.pushState({}, '', url);
                
                // Fetch filtered data
                fetchApplications(url.toString());
            });
        });
    }
}

function setupSearch() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const searchInput = document.getElementById('searchInput');
            const searchValue = searchInput.value.trim();
            
            if (searchValue) {
                // Update URL with search parameter
                const url = new URL(window.location);
                url.searchParams.set('search', searchValue);
                window.history.pushState({}, '', url);
                
                // Fetch search results
                fetchApplications(url.toString());
            }
        });
    }
}

function setupPagination() {
    const paginationLinks = document.querySelectorAll('.pagination-link');
    if (paginationLinks.length) {
        paginationLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                const url = this.getAttribute('href');
                if (url) {
                    window.history.pushState({}, '', url);
                    fetchApplications(url);
                }
            });
        });
    }
}

function setupStatusUpdates() {
    const statusSelects = document.querySelectorAll('.status-select');
    if (statusSelects.length) {
        statusSelects.forEach(select => {
            select.addEventListener('change', function() {
                const applicationId = this.dataset.applicationId;
                const newStatus = this.value;
                
                fetch('/admin/update-application-status/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        application_id: applicationId,
                        status: newStatus
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show status updated notification
                        showNotification('Status updated successfully!', 'success');
                    } else {
                        // Show error notification
                        showNotification('Error updating status: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification('An error occurred while updating the status.', 'error');
                });
            });
        });
    }
}

function fetchApplications(url) {
    // Show loading indicator
    const applicationsContainer = document.getElementById('applicationsContainer');
    if (applicationsContainer) {
        applicationsContainer.innerHTML = '<div class="loading">Loading...</div>';
        
        fetch(url)
            .then(response => response.text())
            .then(html => {
                // Replace the container content with new HTML
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContainer = doc.getElementById('applicationsContainer');
                
                if (newContainer) {
                    applicationsContainer.innerHTML = newContainer.innerHTML;
                    
                    // Re-attach event listeners
                    setupStatusUpdates();
                    setupPagination();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                applicationsContainer.innerHTML = '<div class="error">Failed to load applications. Please try again.</div>';
            });
    }
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Append to body
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('hide');
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