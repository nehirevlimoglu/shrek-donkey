function setupJobActions() {
    // Edit job button
    const editJobBtn = document.querySelector('.edit-job');
    if (editJobBtn) {
        editJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            window.location.href = `/admin_edit_job/${jobId}/`;
        });
    }

    // Delete job button
    const deleteJobBtn = document.querySelector('.delete-job');
    if (deleteJobBtn) {
        deleteJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showModal('Are you sure you want to delete this job?', () => {
                fetch(`/admin_delete_job/${jobId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success || data.status === 'success') {
                        window.location.href = '/admin_job_listings/';
                    } else {
                        alert('Error deleting job: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting the job.');
                });
            });
        });
    }

    // Close job button
    const closeJobBtn = document.querySelector('.close-job');
    if (closeJobBtn) {
        closeJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showModal('Are you sure you want to close this job?', () => {
                updateJobStatus(jobId, 'Closed');
            });
        });
    }

    // Reopen job button
    const reopenJobBtn = document.querySelector('.reopen-job');
    if (reopenJobBtn) {
        reopenJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showModal('Are you sure you want to reopen this job?', () => {
                updateJobStatus(jobId, 'Open');
            });
        });
    }

    // Approve job button
    const approveJobBtn = document.querySelector('.approve-job');
    if (approveJobBtn) {
        approveJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showModal('Are you sure you want to approve this job?', () => {
                updateJobStatus(jobId, 'Approved');
            });
        });
    }
}

// Function to display the modal and handle confirmation
function showModal(message, confirmCallback) {
    const modal = document.getElementById('actionModal');
    const modalMessage = document.getElementById('modalMessage');
    const okButton = document.getElementById('modalOkButton');
    
    modalMessage.textContent = message;
    modal.style.display = 'block';
    
    // Add event listener to the OK button to trigger the callback
    okButton.onclick = function() {
        confirmCallback(); // Execute the provided callback function (e.g., updateJobStatus)
        closeModal(); // Close the modal after action
    };
}

// Function to close the modal
function closeModal() {
    const modal = document.getElementById('actionModal');
    modal.style.display = 'none';
}
