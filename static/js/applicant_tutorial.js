document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Applicant Tutorial Script Loaded!");

    // ✅ Check if 'newUser=true' exists in the URL query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const newApplicant = urlParams.get("newUser") === "true";

    console.log("🔍 newApplicant =", newApplicant); // Debugging check

    if (newApplicant) {
        console.log("🚀 Starting Applicant Tutorial...");
        setTimeout(() => {
            startApplicantTutorial();
        }, 500); // ✅ Delay to ensure elements are fully loaded

        // ✅ Remove 'newUser' from the URL without refreshing the page
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    } else {
        console.log("❌ newApplicant is false, skipping tutorial.");
    }
});

function startApplicantTutorial() {
    console.log("🔧 Ensuring Intro.js Styles Are Applied...");

    introJs().setOptions({
        steps: [
            {
                intro: "👋 Welcome to your Applicant Dashboard! Let’s take a quick tour."
            },
            {
                element: ".filter-options",
                intro: "🔎 Use these filters to find jobs based on location, salary, job type, and company.",
                position: "bottom"
            },
            {
                element: ".job-listings-container",
                intro: "📄 Here you can see all available job listings.",
                position: "top"
            },
            {
                element: ".favorite-star",
                intro: "⭐ Click this star to save jobs to your favorites for easy access later.",
                position: "right"
            },
            {
                element: ".btn-primary",
                intro: "👀 Click 'View Details' to see more information about the job.",
                position: "top"
            },
            {
                intro: "🎉 That's it! Now you can browse and apply for jobs efficiently!"
            }
        ],
        showProgress: true,
        scrollToElement: true,
        disableInteraction: false,
        exitOnOverlayClick: false,
        nextLabel: "Next →",
        prevLabel: "← Back",
        doneLabel: "Finish ✅"
    }).start();
}
