console.log("✅ job_application.js loaded!");

document.addEventListener("DOMContentLoaded", function () {
  const applyBtn = document.getElementById("apply-btn");
  let appliedMsg = document.getElementById("applied-msg");

  // Check if URL indicates that the user already applied
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("applied") === "true") {
    if (applyBtn) {
      applyBtn.style.display = "none";
    }
    if (!appliedMsg) {
      appliedMsg = document.createElement("p");
      appliedMsg.id = "applied-msg";
      appliedMsg.classList.add("already-applied-msg");
      appliedMsg.innerText = "You have already applied for this job.";
      document.querySelector(".button-container").appendChild(appliedMsg);
    } else {
      appliedMsg.style.display = "block";
    }
  }

  // Only add event listener if the button is visible and URL doesn't have applied=true
  if (applyBtn && urlParams.get("applied") !== "true") {
    applyBtn.addEventListener("click", function (event) {
      event.preventDefault(); // Prevent any default action
      const jobId = applyBtn.getAttribute("data-job-id");
      console.log("🟢 Apply button clicked for job id:", jobId);

      // Send AJAX request to apply for the job
      fetch(`/job/${jobId}/apply/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({}) // Send extra data if needed
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          console.log("✅ Application submitted successfully via AJAX");
          // Hide the Apply button
          applyBtn.style.display = "none";
          // Create or show the message element
          if (!appliedMsg) {
            appliedMsg = document.createElement("p");
            appliedMsg.id = "applied-msg";
            appliedMsg.classList.add("already-applied-msg");
            appliedMsg.innerText = "You have already applied for this job.";
            applyBtn.parentNode.appendChild(appliedMsg);
          } else {
            appliedMsg.style.display = "block";
          }
          // Update URL so that a refresh shows the message
          window.history.replaceState(null, "", window.location.pathname + "?applied=true");
        } else {
          console.error("❌ Error applying:", data.error);
          alert("Error: " + (data.error || "Could not submit application."));
        }
      })
      .catch(error => console.error("🔴 Fetch Error:", error));
    });
  } else {
    console.log("❌ Apply button NOT found or application already submitted.");
  }
});

// Helper function to get CSRF token from cookies
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
