console.log("✅ job_application.js loaded!");

document.addEventListener("DOMContentLoaded", function () {
    const applyBtn = document.getElementById("apply-btn");

    if (applyBtn) {
        console.log("✅ Apply button found:", applyBtn);

        applyBtn.addEventListener("click", function () {
            console.log("🟢 Apply button clicked! Processing application...");

            const jobId = applyBtn.getAttribute("data-job-id");

            // Send POST request to our Django view
            fetch(`/job/${jobId}/apply/`, {  
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({}),
            })
            .then(response => response.json())
            .then(data => {
                // If success = true, check whether we already applied
                if (data.success) {
                    if (data.already_applied) {
                        // ✅ Disable button + show "Already Applied"
                        console.log("❌ User already applied. Updating button...");
                        applyBtn.textContent = "Already Applied";
                        applyBtn.disabled = true;
                        applyBtn.classList.add("btn-disabled");
                    } else {
                        // ✅ User just applied for the first time => redirect
                        console.log("✅ Job applied successfully! Redirecting to the application form...");
                        window.location.href = data.redirect_url;
                    }
                } else {
                    // Some other error (invalid request method, etc.)
                    console.warn("⚠️ Something went wrong:", data.error);
                }
            })
            .catch(error => console.error("🔴 Fetch Error:", error));
        });
    } else {
        console.log("❌ Apply button NOT found");
    }
});

// Helper function to get CSRF token
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
