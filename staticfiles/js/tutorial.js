document.addEventListener("DOMContentLoaded", function () {
    // Check if 'newUser=true' exists in the URL query parameters
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("newUser") === "true") {
        startTutorial();  // Start tutorial for new users
        
        // Remove 'newUser' from the URL without refreshing the page
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
});

function startTutorial() {
    introJs().setOptions({
        steps: [
            {
                intro: "👋 Welcome to your Employer Dashboard! Let's take a quick tour."
            },
            {
                element: ".sidebar",
                intro: "📂 This is your navigation sidebar. Use it to move between different sections like Dashboard, Job Listings, Reports, and Settings."
            },
            {
                element: "header",
                intro: "👋 Here you'll find a personalized welcome message and the log-out button."
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
                intro: "📝 Click here to review an applicant’s profile and take further actions."
            },
            {
                intro: "🎉 That's it! You are ready to manage your jobs and applicants efficiently!"
            }
        ],
        showProgress: true,
        showBullets: false,
        exitOnOverlayClick: false,
        nextLabel: "Next →",
        prevLabel: "← Back",
        doneLabel: "Finish ✅"
    }).start();
}
