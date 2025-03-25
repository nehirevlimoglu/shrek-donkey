document.addEventListener("DOMContentLoaded", function () {
    const jobTitles = JSON.parse(document.getElementById("job_titles_json").textContent);
    const jobApplicants = JSON.parse(document.getElementById("job_applicants_json").textContent);
    const jobInterviews = JSON.parse(document.getElementById("job_interviews_json").textContent);

    // Get last 5 entries
    const lastFiveTitles = jobTitles.slice(-5);
    const lastFiveApplicants = jobApplicants.slice(-5);
    const lastFiveInterviews = jobInterviews.slice(-5);

    // Build display labels (acronym only if title has more than one word)
    const displayLabels = lastFiveTitles.map(title => {
        const words = title.trim().split(/\s+/);
        return words.length > 1
            ? words.map(word => word[0].toUpperCase()).join("") // Acronym
            : title; // Keep full
    });

        console.log("✅ Job Titles:", jobTitles);
        console.log("✅ Applicants Data:", jobApplicants);
        console.log("✅ Interviews Data:", jobInterviews);

        if (jobTitles.length === 0 || jobApplicants.length === 0) {
            console.warn("⚠ No applicant data available.");
            return;
        }

        // Applicants Chart (Bar Chart)
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
                responsive: false,
                maintainAspectRatio: true,
                aspectRatio: 2, // Set a custom aspect ratio (width:height = 2:1)
                plugins: {
                    legend: { display: true },
                    tooltip: { enabled: true }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Log canvas size after rendering
        const canvas1 = document.getElementById("applicantsChart");
        console.log("Canvas (Applicants) size after rendering:", canvas1.getBoundingClientRect());

        // Interviews Chart (Pie Chart)
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
                maintainAspectRatio: true,
                aspectRatio: 2, // Set a custom aspect ratio (width:height = 2:1)
                plugins: {
                    legend: { position: "top" },
                    tooltip: { enabled: true }
                }
            }
        });

        // Log canvas size after rendering
        const canvas2 = document.getElementById("interviewsChart");
        console.log("Canvas (Interviews) size after rendering:", canvas2.getBoundingClientRect());

    } catch (error) {
        console.error("❌ JSON Parsing Error:", error);
    // Gradient utility
    function createGradient(ctx, color1, color2) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        return gradient;
    }

    // === Bar Chart: Applicants Per Job ===
    const ctx1 = document.getElementById("applicantsChart").getContext("2d");
    const gradientBlue = createGradient(ctx1, "#60A5FA", "#3B82F6");

    new Chart(ctx1, {
        type: "bar",
        data: {
            labels: displayLabels,
            datasets: [{
                label: "Applicants",
                data: lastFiveApplicants,
                backgroundColor: gradientBlue,
                borderRadius: 10,
                barThickness: 40,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function (tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            return lastFiveTitles[index];
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: "#1E293B"
                    },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#1E293B",
                        stepSize: 1, // 👈 Integers only
                        precision: 0
                    },
                    grid: { color: "#E5E7EB" }
                }
            }
        }
    });

    // === Pie Chart: Interviews Per Job ===
    const ctx2 = document.getElementById("interviewsChart").getContext("2d");
    const niceColors = ["#F87171", "#FBBF24", "#34D399", "#60A5FA", "#A78BFA"];

    new Chart(ctx2, {
        type: "pie",
        data: {
            labels: lastFiveTitles,
            datasets: [{
                label: "Interviews",
                data: lastFiveInterviews,
                backgroundColor: niceColors,
                borderColor: "#FFF",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        boxWidth: 12,
                        color: "#1E293B",
                        padding: 12
                    }
                },
                tooltip: {
                    backgroundColor: "#1E293B",
                    titleColor: "#FFF",
                    bodyColor: "#E2E8F0"
                }
            }
        }
    });
});
