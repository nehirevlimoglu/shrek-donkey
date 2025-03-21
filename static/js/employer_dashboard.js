// Listen for DOM load
document.addEventListener("DOMContentLoaded", function () {
    // 1. If newUser param is in URL, start tutorial
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("newUser") === "true") {
        startTutorial();
        // Remove 'newUser' from URL
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }

    // 2. Attach click listener to any .review-button
    document.querySelectorAll(".review-button").forEach(button => {
        button.addEventListener("click", function () {
            let applicationId = this.getAttribute("data-applicant");
            window.location.href = `/review-application/${applicationId}/`;
        });
    });

    // 3. Attach click listener to any .seen-btn
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

// The tutorial function
function startTutorial() {
    introJs().setOptions({
        steps: [
            { intro: "👋 Welcome to your Employer Dashboard! Let's take a quick tour." },
            {
                element: ".sidebar",
                intro: "📂 This is your navigation sidebar..."
            },
            {
                element: "header",
                intro: "👋 Here you'll find a personalized welcome message..."
            },
            {
                element: "#total-jobs",
                intro: "📌 This shows the total number of jobs you've posted."
            },
            {
                element: "#active-listings",
                intro: "🔥 These are your currently active job listings."
            },
            {
                element: "#total-applicants",
                intro: "👥 Here you can see the total number of applicants."
            },
            {
                element: "#recent-applicants",
                intro: "🔎 This section displays the most recent applicants."
            },
            {
                element: "#review-button",
                intro: "📝 Click here to review an applicant’s profile..."
            },
            { intro: "🎉 That's it! You are ready to manage your jobs and applicants efficiently!" }
        ],
        showProgress: true,
        showBullets: false,
        exitOnOverlayClick: false,
        nextLabel: "Next →",
        prevLabel: "← Back",
        doneLabel: "Finish ✅"
    }).start();
}

// Mark a notification as read
function markEmployerNotificationAsRead(notificationId, buttonElement) {
    fetch(`/mark-notification-read/${notificationId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({}) // or any payload you need
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            let notificationElement = document.getElementById(`notification-${notificationId}`);
            if (notificationElement) {
                notificationElement.classList.remove("unread");
                notificationElement.style.opacity = "0.9";

                // Replace button with "✔ Seen" text
                let seenText = document.createElement("span");
                seenText.textContent = "✔ Seen";
                seenText.classList.add("seen-text");
                buttonElement.replaceWith(seenText);
            }
        } else {
            console.error("Error marking notification as read:", data.error);
        }
    })
    .catch(error => console.error("Request failed:", error));
}

// Utility to get CSRF token
function getCSRFToken() {
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : "";
}
