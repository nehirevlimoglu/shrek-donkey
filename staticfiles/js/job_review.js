document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ job_application.js loaded");

    const applyBtn = document.getElementById("apply-btn");

    if (applyBtn) {
        console.log("✅ Apply button found:", applyBtn);

        applyBtn.addEventListener("click", function () {
            console.log("🟢 Apply button clicked!");

            const jobId = applyBtn.getAttribute("data-job-id");
            console.log("🔵 Job ID:", jobId);

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
                console.log("🔵 Server Response:", data);
                
                if (data.success) {
                    console.log("✅ Application submitted successfully!");
                    applyBtn.style.display = "none"; 
                    const message = document.createElement("p");
                    message.classList.add("already-applied-message");
                    message.textContent = "✅ You have already applied for this job.";
                    applyBtn.parentNode.appendChild(message);
                } else {
                    console.log("❌ Error applying: ", data.error);
                    alert("❌ Error: " + data.error);
                }
            })
            .catch(error => console.error("🔴 Fetch Error:", error));
        });
    } else {
        console.log("❌ Apply button NOT found");
    }
});
