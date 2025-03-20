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

       

    } catch (error) {
        console.error("❌ JSON Parsing Error:", error);
    }
});s