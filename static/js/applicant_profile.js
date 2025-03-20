let actionType = '';
let candidateName = '';
let jobTitle = '';

function confirmAction(action, name, job) {
    actionType = action;
    candidateName = name;
    jobTitle = job;

    const title = action === 'accept' ? 'Confirm Hiring' : 'Confirm Rejection';
    const message = action === 'accept' 
        ? `Are you sure you want to hire ${name} for the job "${job}"?`
        : `Are you sure you want to reject ${name} for the job "${job}"?`;

    document.getElementById('confirmation-title').innerText = title;
    document.getElementById('confirmation-message').innerText = message;
    document.getElementById('confirmation-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('confirmation-modal').style.display = 'none';
}

window.confirmActionFinal = function () {
    let candidateId = document.getElementById("candidate-id").value;  // Get actual value from HTML

    let url = actionType === 'accept' 
        ? `/candidates/${candidateId}/accept/`  
        : `/candidates/${candidateId}/reject/`; 

    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),  
            "Content-Type": "application/json"
        },
        body: JSON.stringify({})  // Empty body needed for Django to accept POST request
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error("Failed to update status.");
    })
    .then(data => {
        console.log("✅ Status Updated:", data);
        location.reload();  // Refresh page after update
    })
    .catch(error => {
        console.error("❌ Error updating status:", error);
    });
}

// Function to get CSRF token
function getCSRFToken() {
    let cookieValue = null;
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length, cookie.length);
            break;
        }
    }
    return cookieValue;
}
