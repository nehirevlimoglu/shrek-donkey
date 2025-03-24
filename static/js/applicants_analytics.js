document.addEventListener("DOMContentLoaded", function () {
    console.log("📊 Chart.js: Script loaded and DOM ready");

    const labelsEl = document.getElementById("offerLabels");
    const dataEl = document.getElementById("offerData");
    const colorsEl = document.getElementById("offerColors");
    const canvas = document.getElementById("offerChart");

    if (!labelsEl || !dataEl || !colorsEl) {
        console.error("🚨 Missing JSON data elements");
        return;
    }

    const offerLabels = JSON.parse(labelsEl.textContent);
    const offerData = JSON.parse(dataEl.textContent);
    const offerColors = JSON.parse(colorsEl.textContent);

    console.log("✅ offerLabels:", offerLabels);
    console.log("✅ offerData:", offerData);
    console.log("✅ offerColors:", offerColors);

    if (!canvas) {
        console.error("🚨 No canvas element found with ID 'offerChart'");
        return;
    }

    const ctx = canvas.getContext("2d");

    console.log("🎨 Initializing pie chart...");
    new Chart(ctx, {
        type: "pie",
        data: {
            labels: offerLabels,
            datasets: [{
                data: offerData,
                backgroundColor: offerColors
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "top"
                }
            }
        }
    });
});
