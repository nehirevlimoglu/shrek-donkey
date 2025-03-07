document.addEventListener("DOMContentLoaded", function () {
    const applyBtn = document.getElementById("apply-btn");

    if (applyBtn) {
        applyBtn.addEventListener("click", function () {
            const jobId = applyBtn.getAttribute("data-job-id");

            fetch(`/apply-for-job/${jobId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({}),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // ✅ Hide the button and show success message
                    applyBtn.style.display = "none";
                    const message = document.createElement("p");
                    message.classList.add("already-applied-message");
                    message.textContent = "✅ You have already applied for this job.";
                    applyBtn.parentNode.appendChild(message);
                } else {
                    alert("❌ Error: " + data.error);
                }
            })
            .catch(error => console.error("Error:", error));
        });
    }
});

// ✅ Function to get CSRF Token for AJAX
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}