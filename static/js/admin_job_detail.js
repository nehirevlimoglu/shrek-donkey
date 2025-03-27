document.addEventListener('DOMContentLoaded', function() {
    // Job action buttons
    setupJobActions();
    
    // Candidate view button
    setupCandidateView();
});

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
            showConfirmationModal({
                title: 'Delete Job?',
                message: 'Are you sure you want to delete this job listing? This action cannot be undone.',
                onConfirm: () => {
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
                            showConfirmationModal({
                                title: 'Error Deleting Job',
                                message: data.error || 'Unknown error'
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showConfirmationModal({
                            title: 'Error',
                            message: 'An error occurred while deleting the job.'
                        });
                    });
                }
            });
        });
    }
    
    // Close job button
    const closeJobBtn = document.querySelector('.close-job');
    if (closeJobBtn) {
        closeJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showConfirmationModal({
                title: 'Close Job?',
                message: 'Are you sure you want to close this job?',
                onConfirm: () => {
                    updateJobStatus(jobId, 'Closed');
                }
            });
        });
    }
    
    // Reopen job button
    const reopenJobBtn = document.querySelector('.reopen-job');
    if (reopenJobBtn) {
        reopenJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showConfirmationModal({
                title: 'Reopen Job?',
                message: 'Are you sure you want to reopen this job?',
                onConfirm: () => {
                    updateJobStatus(jobId, 'Open');
                }
            });
        });
    }
    
    // Approve job button
    const approveJobBtn = document.querySelector('.approve-job');
    if (approveJobBtn) {
        approveJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showConfirmationModal({
                title: 'Approve Job?',
                message: 'Are you sure you want to approve this job?',
                onConfirm: () => {
                    updateJobStatus(jobId, 'Approved');
                }
            });
        });
    }
}

function updateJobStatus(jobId, status) {
    console.log(`Sending request to update job ${jobId} to status: ${status}`);
    
    fetch(`/admin_toggle_job_status/${jobId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => {
        console.log(`Received response with status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            updateJobStatusUI(status);
            console.log('Scheduling page reload in 1.5 seconds...');
            setTimeout(() => {
                console.log('Reloading page now...');
                window.location.reload();
            }, 1500);
        } else {
            showConfirmationModal({
                title: 'Error Updating Job Status',
                message: data.error || 'Unknown error'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showConfirmationModal({
            title: 'Error',
            message: 'An error occurred while updating the job status.'
        });
    });
}

function updateJobStatusUI(status) {
    console.log(`Updating UI for status: ${status}`);
    const statusBadge = document.querySelector('.job-header .badge');
    if (statusBadge) {
        if (status === 'Open') {
            statusBadge.textContent = 'Open';
            statusBadge.classList.remove('closed');
            statusBadge.classList.add('open');
            console.log('Updated badge to Open');
        } else if (status === 'Closed') {
            statusBadge.textContent = 'Closed';
            statusBadge.classList.remove('open');
            statusBadge.classList.add('closed');
            console.log('Updated badge to Closed');
        } else if (status === 'Approved') {
            const approvalStatus = document.querySelector('.approval-status');
            if (approvalStatus) {
                approvalStatus.textContent = 'Approved';
                approvalStatus.classList.remove('pending');
                approvalStatus.classList.add('approved');
                console.log('Updated approval status to Approved');
            }
        }
    } else {
        console.warn('Status badge not found in the DOM');
    }
    
    const closeJobBtn = document.querySelector('.close-job');
    const reopenJobBtn = document.querySelector('.reopen-job');
    if (closeJobBtn && reopenJobBtn) {
        if (status === 'Open') {
            closeJobBtn.style.display = 'inline-block';
            reopenJobBtn.style.display = 'none';
            console.log('Showing Close button, hiding Reopen button');
        } else if (status === 'Closed') {
            closeJobBtn.style.display = 'none';
            reopenJobBtn.style.display = 'inline-block';
            console.log('Hiding Close button, showing Reopen button');
        }
    } else {
        console.warn('Close/Reopen buttons not found in the DOM');
    }
    
    if (status === 'Approved') {
        const approveJobBtn = document.querySelector('.approve-job');
        if (approveJobBtn) {
            approveJobBtn.style.display = 'none';
            console.log('Hiding Approve button');
        }
    }
}

function setupCandidateView() {
    const viewCandidateBtns = document.querySelectorAll('.view-candidate-btn');
    viewCandidateBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const candidateId = this.dataset.candidateId;
            console.log(`Fetching candidate info for ID: ${candidateId}`);
            
            fetch(`/admin_get-candidate-info/${candidateId}/`)
                .then(response => {
                    console.log(`Response status: ${response.status}`);
                    if (!response.ok) {
                        throw new Error(`Server responded with status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Received candidate data:', data);
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
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };
        
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
        console.log(`Updating candidate ${candidateId} status to: ${newStatus}`);
        
        fetch(`/admin_update-candidate-status/${candidateId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => {
            console.log(`Update status response: ${response.status}`);
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Update status response data:', data);
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
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

// Custom confirmation modal function
function showConfirmationModal(options) {
    let confirmModal = document.getElementById('confirmModal');
    if (!confirmModal) {
        // Create the modal
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
    
    // Set the modal title and message
    document.getElementById('confirmModalTitle').textContent = options.title || 'Confirm';
    document.getElementById('confirmModalMessage').textContent = options.message || 'Are you sure?';
    
    // Display the modal
    confirmModal.style.display = 'block';
    
    // Set up the button actions
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
