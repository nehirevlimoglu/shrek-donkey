function toggleDropdown(id) {
    document.getElementById(id).classList.toggle("show");
}

window.onclick = function(event) {
    if (!event.target.matches('.review-btn')) {
        var dropdowns = document.getElementsByClassName("dropdown-content");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
};

function updateStatus(jobId, status) {
    console.log("Updating status for job:", jobId, "to", status); // Debugging
    fetch('/update-job-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),  // Ensure CSRF protection
        },
        body: JSON.stringify({
            job_id: jobId,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('status-' + jobId).innerText = status;
            document.getElementById('status-' + jobId).className = 'status-label ' + (status === 'Approved' ? 'status-approved' : 'status-rejected');
            document.getElementById('dropdown-' + jobId).classList.remove('show');
            document.getElementById('action-buttons-' + jobId).style.display = 'none';
        } else {
            alert("Error updating status. Please try again.");
        }
    })
    .catch(error => console.error('Error:', error));
}

// Function to get CSRF token (required for Django POST requests)
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}
