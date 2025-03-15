// ✅ Ensure the function is globally available
window.startApplicantTutorial = function () {
    console.log("🔧 Ensuring Intro.js Styles Are Applied...");

    introJs().setOptions({
        steps: [
            { intro: "👋 Welcome to your Applicant Dashboard! Let’s take a quick tour." },
            { element: ".filter-options", intro: "🔎 Use these filters to refine job listings based on location, salary, type, and company.", position: "bottom" },
            { element: ".job-table thead", intro: "📄 This table displays all the available job listings that match your filters.", position: "bottom" },
            { element: ".job-listings td:nth-child(6)", intro: "⭐ Click the star icon to mark a job as your favorite for easy access later.", position: "right" },
            { element: ".job-listings td:nth-child(7) a", intro: "👀 Click 'View Details' to see the full job description and application instructions.", position: "left" },
            { intro: "🎉 That's it! You are now ready to explore and apply for jobs. Good luck!" }
        ],
        showProgress: true,
        scrollToElement: true,
        disableInteraction: false,
        exitOnOverlayClick: false,
        nextLabel: "Next →",
        prevLabel: "← Back",
        doneLabel: "Finish ✅"
    }).start();
};

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
            { intro: "👋 Welcome to your Applicant Dashboard! Let’s take a quick tour." },
            { element: ".filter-options", intro: "🔎 Use these filters to refine job listings based on location, salary, type, and company.", position: "bottom" },
            { element: ".job-table thead", intro: "📄 This table displays all the available job listings that match your filters.", position: "bottom" },
            { element: ".job-listings td:nth-child(6)", intro: "⭐ Click the star icon to mark a job as your favorite for easy access later.", position: "right" },
            { element: ".job-listings td:nth-child(7) a", intro: "👀 Click 'View Details' to see the full job description and application instructions.", position: "left" },
            { intro: "🎉 That's it! You are now ready to explore and apply for jobs. Good luck!" }
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
