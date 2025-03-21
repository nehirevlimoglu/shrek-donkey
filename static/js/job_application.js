console.log("✅ job_application.js loaded!");

document.addEventListener("DOMContentLoaded", function () {
  const applyBtn = document.getElementById("apply-btn");
  const alreadyAppliedMsg = document.getElementById("already-applied-msg");

  if (applyBtn) {
    console.log("✅ Apply button found:", applyBtn);
    
    applyBtn.addEventListener("click", function (event) {
      event.preventDefault(); // Prevent the default form submission
      console.log("🟢 Apply button clicked! Submitting form...");

      // Add delay before showing the "Already Applied" message
      setTimeout(() => {
        console.log("⏳ Waiting before showing 'Already Applied' message...");

        // Hide the "Apply Now" button
        applyBtn.style.display = "none";
        console.log("✅ 'Apply Now' button hidden");

        // Check if the message element exists before trying to show it
        if (alreadyAppliedMsg) {
          alreadyAppliedMsg.style.display = "block";  // Show the "Already Applied" message
          console.log("✅ Showing 'Already Applied' message");
        } else {
          console.log("❌ 'Already Applied' message element not found");
          
          // Create the message if it doesn't exist
          const newMsg = document.createElement("p");
          newMsg.id = "already-applied-msg";
          newMsg.textContent = "You have already applied for this job";
          newMsg.style.fontStyle = "italic";
          
          // Insert the message after the form
          const form = applyBtn.closest("form");
          form.parentNode.insertBefore(newMsg, form.nextSibling);
          console.log("✅ Created new 'Already Applied' message");
        }

        // Keep the "Already Applied" message visible for 3 seconds (3000ms)
        setTimeout(() => {
          console.log("⏳ Hiding 'Already Applied' message after delay...");
          // Hide the "Already Applied" message after the delay
          alreadyAppliedMsg.style.display = "none";  // or newMsg.style.display = "none"; if it's a new element
          console.log("✅ Hiding 'Already Applied' message after delay");
        }, 3000); // Adjust time as needed (3 seconds)

      }, 500); // Delay before showing the "Already Applied" message (500ms)
    });
  } else {
    console.log("❌ Apply button NOT found");
  }
});

// Helper function to get CSRF token - keeping your original implementation
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
