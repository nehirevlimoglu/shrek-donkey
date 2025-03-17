document.addEventListener("DOMContentLoaded", function () {
    try {
        // ✅ Ensure script elements exist before parsing
        const jobTitlesElement = document.getElementById("job_titles_json");
        const jobApplicantsElement = document.getElementById("job_applicants_json");
        const jobInterviewsElement = document.getElementById("job_interviews_json");

        if (!jobTitlesElement || !jobApplicantsElement || !jobInterviewsElement) {
            console.error("❌ Missing JSON script elements.");
            return;
        }

        // ✅ Parse JSON safely
        const jobTitles = JSON.parse(jobTitlesElement.textContent);
        const jobApplicants = JSON.parse(jobApplicantsElement.textContent);
        const jobInterviews = JSON.parse(jobInterviewsElement.textContent);

        console.log("✅ Job Titles:", jobTitles);
        console.log("✅ Applicants Data:", jobApplicants);
        console.log("✅ Interviews Data:", jobInterviews);

        if (jobTitles.length === 0 || jobApplicants.length === 0) {
            console.warn("⚠ No applicant data available.");
            return;
        }

        // ✅ Initialize Applicants Chart (Bar Chart)
        const ctx1 = document.getElementById("applicantsChart").getContext("2d");
        new Chart(ctx1, {
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
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true },
                    tooltip: { enabled: true }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // ✅ Initialize Interviews Chart (Pie Chart)
        const ctx2 = document.getElementById("interviewsChart").getContext("2d");
        new Chart(ctx2, {
            type: "pie",
            data: {
                labels: jobTitles,
                datasets: [{
                    label: "Interviews Per Job",
                    data: jobInterviews,
                    backgroundColor: ["#FF5733", "#C70039", "#900C3F"],
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: "top" },
                    tooltip: { enabled: true }
                }
            }
        });

    } catch (error) {
        console.error("❌ JSON Parsing Error:", error);
    }
});
