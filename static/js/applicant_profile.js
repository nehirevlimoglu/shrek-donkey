document.addEventListener("DOMContentLoaded", function () {
    let searchInput = document.getElementById("job-search");
    let dropdownResults = document.querySelector(".dropdown-results");
    let selectElement = document.getElementById("id_job_preferences");

    searchInput.addEventListener("input", function () {
        let searchTerm = searchInput.value.toLowerCase();
        dropdownResults.innerHTML = "";
        if (searchTerm.length > 0) {
            let options = Array.from(selectElement.options);
            let filteredOptions = options.filter(option =>
                option.text.toLowerCase().includes(searchTerm)
            );

            filteredOptions.forEach(option => {
                let div = document.createElement("div");
                div.textContent = option.text;
                div.setAttribute("data-value", option.value);
                div.addEventListener("click", function () {
                    let selectedOption = document.createElement("option");
                    selectedOption.value = option.value;
                    selectedOption.textContent = option.text;
                    selectedOption.selected = true;
                    selectElement.appendChild(selectedOption);
                    searchInput.value = "";
                    dropdownResults.innerHTML = "";
                });
                dropdownResults.appendChild(div);
            });

            dropdownResults.style.display = "block";
        } else {
            dropdownResults.style.display = "none";
        }
    });

    document.addEventListener("click", function (event) {
        if (!searchInput.contains(event.target) && !dropdownResults.contains(event.target)) {
            dropdownResults.style.display = "none";
        }
    });
});

let selectedAction = null;
let selectedCandidateId = null;

function confirmAction(action, applicantName, jobTitle) {
    selectedAction = action;
    selectedCandidateId = document.getElementById('candidate-id').value;

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

    const url = `/candidates/${selectedCandidateId}/${selectedAction}/`;  // Update path if needed
    const csrfToken = getCookie('csrftoken');

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
            // Update chip text & style
            const chip = document.querySelector(".chip");
            chip.innerText = data.status;
            chip.className = "chip " + (data.status === 'Hired' ? 'chip-accepted' : 'chip-rejected');

            // Hide buttons
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

// Grab CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const cookieTrimmed = cookie.trim();
            if (cookieTrimmed.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookieTrimmed.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
