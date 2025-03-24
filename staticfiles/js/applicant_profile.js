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

    document.getElementById('confirmation-title').innerText = title;
    document.getElementById('confirmation-message').innerText = message;
    document.getElementById('confirmation-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('confirmation-modal').style.display = 'none';
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
            const chip = document.querySelector(".chip");
            chip.innerText = data.status;
            chip.className = "chip " + (data.status === 'Hired' ? 'chip-accepted' : 'chip-rejected');

            const buttons = document.querySelector(".action-buttons");
            if (buttons) buttons.style.display = "none";

            const interviewBtn = document.querySelector(".btn-primary");
            if (interviewBtn) interviewBtn.style.display = "none";
        } else if (data.error) {
            alert(data.error);
        }

        closeModal();
    })
    .catch(error => {
        console.error("Error updating candidate status:", error);
        alert("Something went wrong. Please try again.");
        closeModal();
    });
}

// Expose functions to global scope so inline HTML can access them
window.confirmAction = confirmAction;
window.confirmActionFinal = confirmActionFinal;
window.closeModal = closeModal;
