console.log("✅ job_application.js loaded!");

document.addEventListener("DOMContentLoaded", function () {
    const applyBtn = document.getElementById("apply-btn");

    if (applyBtn) {
        console.log("✅ Apply button found:", applyBtn);

        applyBtn.addEventListener("click", function () {
            console.log("🟢 Apply button clicked! Submitting form...");

            const form = document.createElement("form"); // Create a new form element
            form.method = "POST";
            form.action = `/job/${applyBtn.getAttribute("data-job-id")}/apply/`;
            form.enctype = "multipart/form-data"; // Ensure file upload works

            // Add CSRF token
            const csrfInput = document.createElement("input");
            csrfInput.type = "hidden";
            csrfInput.name = "csrfmiddlewaretoken";
            csrfInput.value = getCookie("csrftoken");
            form.appendChild(csrfInput);

            document.body.appendChild(form);
            form.submit();
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
