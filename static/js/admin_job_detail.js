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
            window.location.href = `/admin/edit-job/${jobId}/`;
        });
    }
    
    // Delete job button
    const deleteJobBtn = document.querySelector('.delete-job');
    if (deleteJobBtn) {
        deleteJobBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            if (confirm('Are you sure you want to delete this job listing? This action cannot be undone.')) {
                fetch(`/admin/delete-job/${jobId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = '/admin/job-listings/';
                    } else {
                        alert('Error deleting job: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting the job.');
                });
            }
        });
    }
    
    // Close job button
    const closeJobBtn = document.querySelector('.close-job');
    if (closeJobBtn) {
        closeJobBtn.addEventListener('click', function() {
            updateJobStatus(this.dataset.jobId, 'Closed');
        });
    }
    
    // Reopen job button
    const reopenJobBtn = document.querySelector('.reopen-job');
    if (reopenJobBtn) {
        reopenJobBtn.addEventListener('click', function() {
            updateJobStatus(this.dataset.jobId, 'Open');
        });
    }
    
    // Approve job button
    const approveJobBtn = document.querySelector('.approve-job');
    if (approveJobBtn) {
        approveJobBtn.addEventListener('click', function() {
            updateJobStatus(this.dataset.jobId, 'Approved');
        });
    }
}

function updateJobStatus(jobId, status) {
    fetch(`/admin/update-job-status/${jobId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Error updating job status: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the job status.');
    });
}

function setupCandidateView() {
    // View candidate buttons
    const viewCandidateBtns = document.querySelectorAll('.view-candidate-btn');
    viewCandidateBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const candidateId = this.dataset.candidateId;
            fetch(`/admin/get-candidate-info/${candidateId}/`)
                .then(response => response.json())
                .then(data => {
                    displayCandidateModal(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while fetching candidate information.');
                });
        });
    });
}

function displayCandidateModal(candidateData) {
    // Create modal if it doesn't exist
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
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };
    }
    
    // Update modal content with candidate data
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
                <option value="Reviewing" ${candidateData.status === 'Reviewing' ? 'selected' : ''}>Reviewing</option>
                <option value="Interview" ${candidateData.status === 'Interview' ? 'selected' : ''}>Interview</option>
                <option value="Offered" ${candidateData.status === 'Offered' ? 'selected' : ''}>Offered</option>
                <option value="Rejected" ${candidateData.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                <option value="Hired" ${candidateData.status === 'Hired' ? 'selected' : ''}>Hired</option>
            </select>
            <button class="update-btn" data-candidate-id="${candidateData.id}">Update Status</button>
        </div>
    `;
    
    // Add event listener for status update button
    const updateBtn = candidateInfo.querySelector('.update-btn');
    updateBtn.addEventListener('click', function() {
        const candidateId = this.dataset.candidateId;
        const newStatus = document.getElementById('applicationStatus').value;
        
        fetch(`/admin/update-candidate-status/${candidateId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal and reload page to see updated status
                modal.style.display = 'none';
                window.location.reload();
            } else {
                alert('Error updating status: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating the candidate status.');
        });
    });
    
    // Show the modal
    modal.style.display = 'block';
}

// Helper function to get CSRF token from cookies
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
} 