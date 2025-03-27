console.log("✅ applicant_profile.js loaded");

let selectedAction = null;
let selectedCandidateId = null;

function confirmAction(action, applicantName, jobTitle) {
    selectedAction = action;
    selectedCandidateId = document.getElementById('candidate-id').value;

    console.log("📦 Action:", action);
    console.log("👤 Candidate ID:", selectedCandidateId);

    const title = action === 'accept' ? "Accept Applicant" : "Reject Applicant";
    const message = `Are you sure you want to ${action} ${applicantName} for the role "${jobTitle}"?`;

    // Set up the confirmation modal for a normal accept/reject flow
    document.getElementById('confirmation-title').innerText = title;
    document.getElementById('confirmation-message').innerText = message;

    // Show both buttons, with default text
    const confirmBtn = document.getElementById('confirm-button');
    confirmBtn.innerText = "Yes, Proceed";
    confirmBtn.onclick = confirmActionFinal;
    confirmBtn.style.display = "inline-block";

    const cancelBtn = document.getElementById('cancel-button');
    cancelBtn.innerText = "Cancel";
    cancelBtn.onclick = closeModal;
    cancelBtn.style.display = "inline-block";

    // Display the modal
    document.getElementById('confirmation-modal').style.display = 'flex';
}

function showErrorModal(errorMsg) {
    // Set the modal to "Error" mode
    document.getElementById('confirmation-title').innerText = "Error";
    document.getElementById('confirmation-message').innerText = errorMsg;

    // "Yes, Proceed" becomes "OK" (or any label you want)
    const confirmBtn = document.getElementById('confirm-button');
    confirmBtn.innerText = "OK";
    confirmBtn.onclick = closeModal;
    confirmBtn.style.display = "inline-block";

    // Optionally hide the Cancel button or rename it
    const cancelBtn = document.getElementById('cancel-button');
    cancelBtn.style.display = "none";  // hide it entirely

    // Show the modal
    document.getElementById('confirmation-modal').style.display = 'flex';
}

function closeModal() {
    // Hide the modal
    document.getElementById('confirmation-modal').style.display = 'none';

    // Reset the global variables
    selectedAction = null;
    selectedCandidateId = null;
}

function confirmActionFinal() {
    if (!selectedAction || !selectedCandidateId) return;

    const url = `/candidates/${selectedCandidateId}/${selectedAction}/`;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            // Successfully updated
            const chip = document.querySelector(".chip");
            chip.innerText = data.status;
            chip.className = "chip " + (data.status === 'Hired' ? 'chip-accepted' : 'chip-rejected');

            const buttons = document.querySelector(".action-buttons");
            if (buttons) buttons.style.display = "none";

            const interviewBtn = document.querySelector(".btn-primary");
            if (interviewBtn) interviewBtn.style.display = "none";

            closeModal();
        } else if (data.error) {
            // Instead of alert, show error modal
            showErrorModal(data.error);
        }
    })
    .catch(error => {
        console.error("Error updating candidate status:", error);
        showErrorModal("Something went wrong. Please try again.");
    });
}

// Expose functions to global scope so inline HTML can access them
window.confirmAction = confirmAction;
window.confirmActionFinal = confirmActionFinal;
window.closeModal = closeModal;
window.showErrorModal = showErrorModal;
