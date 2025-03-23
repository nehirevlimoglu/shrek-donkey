let selectedAction = null;
let selectedCandidateId = null;

document.addEventListener("DOMContentLoaded", function () {
    const candidateIdField = document.getElementById("candidate-id");
    selectedCandidateId = candidateIdField ? candidateIdField.value : null;

    // 💡 FORCE-HIDE modal on load (in case inline display:flex remains from prior use)
    const modal = document.getElementById("confirmation-modal");
    if (modal) {
        modal.style.display = "none";
    }

    // Prevent "Review" button from triggering modal logic (just in case)
    const reviewLinks = document.querySelectorAll('a.btn-review');
    reviewLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            e.stopImmediatePropagation();
        });
    });
});


function confirmAction(action, applicantName, jobTitle) {
    if (!["accept", "reject"].includes(action)) return;

    if (!action || !selectedCandidateId || !applicantName?.trim() || !jobTitle?.trim() || jobTitle === "None") {
        return;
    }

    const modal = document.getElementById("confirmation-modal");
    const titleEl = document.getElementById("confirmation-title");
    const messageEl = document.getElementById("confirmation-message");

    if (!modal || !titleEl || !messageEl) return;

    titleEl.textContent = action === "accept" ? "Accept Applicant" : "Reject Applicant";
    messageEl.textContent = `Are you sure you want to ${action} ${applicantName} for the role "${jobTitle}"?`;
    modal.style.display = "flex";

    selectedAction = action;
}


function closeModal() {
    document.getElementById("confirmation-modal").style.display = "none";
    selectedAction = null;
}

function confirmActionFinal() {
    if (!selectedAction || !selectedCandidateId) return;

    const url = `/candidates/${selectedCandidateId}/${selectedAction}/`;
    const csrfToken = getCookie("csrftoken");

    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
        }
    })
        .then(res => res.json())
        .then(data => {
            if (data.status) {
                const chip = document.querySelector(".chip");
                if (chip) {
                    chip.innerText = data.status;
                    chip.className = `chip ${data.status === 'Hired' ? 'chip-accepted' : 'chip-rejected'}`;
                }

                document.querySelector(".action-buttons")?.remove();
                document.querySelector(".btn-primary")?.remove();
            } else {
                alert(data.error || "Unexpected error.");
            }
            closeModal();
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Something went wrong. Try again.");
            closeModal();
        });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(trimmed.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
