document.addEventListener("DOMContentLoaded", function () {
    fetch("/static/data/job_titles.json")  // ✅ Load JSON from static folder
        .then(response => response.json())
        .then(jobTitles => {
            let positionDropdown = document.getElementById("position");
            positionDropdown.innerHTML = "";  // Clear default text
            
            jobTitles.forEach(title => {
                let option = document.createElement("option");
                option.value = title;
                option.textContent = title;
                positionDropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error("Error loading job titles:", error);
        });
});
