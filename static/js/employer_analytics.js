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
