// After DOM load, attach click event to .review-button
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".review-button").forEach(button => {
        button.addEventListener("click", function () {
            let applicationId = this.getAttribute("data-applicant");
            window.location.href = `/review-application/${applicationId}/`;
        });
    });
});

// After DOM load, attach click event to .seen-btn
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".seen-btn").forEach(button => {
        button.addEventListener("click", function () {
            let notificationId = this.getAttribute("data-notification-id");
            if (notificationId) {
                markEmployerNotificationAsRead(notificationId, this);
            } else {
                console.error("Notification ID not found.");
            }
        });
    });
});

// Function to mark notification as read
function markEmployerNotificationAsRead(notificationId, buttonElement) {
    fetch(`/mark-notification-read/${notificationId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let notificationElement = document.getElementById(`notification-${notificationId}`);
            if (notificationElement) {
                notificationElement.classList.remove("unread");
                notificationElement.style.opacity = "0.7";  // Make it visually faded

                // Replace the "Seen" button with text
                let seenText = document.createElement("span");
                seenText.textContent = "✔ Seen";
                seenText.style.color = "#28A745";  // Green color for seen status
                seenText.style.fontWeight = "bold";

                buttonElement.replaceWith(seenText);  // Swap button with text
            }
        } else {
            console.error("Error marking notification as read:", data.error);
        }
    })
    .catch(error => console.error("Request failed:", error));
}

// Utility function to fetch CSRF token if needed
function getCSRFToken() {
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : "";
}
