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

function confirmActionFinal() {
    const url = actionType === 'accept' 
        ? "/employer_job_listings"  // Redirect to the job listings page on Accept
        : "/candidates";            // Redirect to the candidates page on Reject

    window.location.href = url;  // This will redirect to the respective page
}