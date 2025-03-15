document.addEventListener("DOMContentLoaded", function () {
    try {
        // ✅ Ensure script elements exist before parsing
        const jobTitlesElement = document.getElementById("job_titles_json");
        const jobApplicantsElement = document.getElementById("job_applicants_json");
        const jobInterviewsElement = document.getElementById("job_interviews_json");

        if (!jobTitlesElement || !jobApplicantsElement || !jobInterviewsElement) {
            console.error("❌ Missing JSON script elements in the HTML.");
            return;
        }

        // ✅ Parse JSON safely (Check for empty values)
        const jobTitles = jobTitlesElement.textContent.trim() ? JSON.parse(jobTitlesElement.textContent) : [];
        const jobApplicants = jobApplicantsElement.textContent.trim() ? JSON.parse(jobApplicantsElement.textContent) : [];
        const jobInterviews = jobInterviewsElement.textContent.trim() ? JSON.parse(jobInterviewsElement.textContent) : [];

        console.log("✅ Job Titles:", jobTitles);
        console.log("✅ Applicants Data:", jobApplicants);
        console.log("✅ Interviews Data:", jobInterviews);

        // ✅ Ensure data exists before rendering charts
        if (jobTitles.length > 0 && jobApplicants.length > 0) {
            new Chart(document.getElementById("applicantsChart").getContext("2d"), {
                type: "bar",
                data: {
                    labels: jobTitles,
                    datasets: [{
                        label: "Applicants Per Job",
                        data: jobApplicants,
                        backgroundColor: ["#1A73E8", "#34A853", "#FBBC05"],
                        borderRadius: 5
                    }]
                },
            });
        } else {
            console.warn("⚠ No applicant data available.");
        }

        if (jobTitles.length > 0 && jobInterviews.length > 0) {
            new Chart(document.getElementById("interviewsChart").getContext("2d"), {
                type: "bar",
                data: {
                    labels: jobTitles,
                    datasets: [{
                        label: "Interviews Per Job",
                        data: jobInterviews,
                        backgroundColor: ["#FF5733", "#C70039", "#900C3F"],
                        borderRadius: 5
                    }]
                },
            });
        } else {
            console.warn("⚠ No interview data available.");
        }
    } catch (error) {
        console.error("❌ JSON Parsing Error:", error);
    }
});
