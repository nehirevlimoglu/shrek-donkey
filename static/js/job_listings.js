function toggleDetails(jobId) {
    let details = document.getElementById("job-details-" + jobId);
    let icon = document.getElementById("toggle-icon-" + jobId);
    
    if (details.style.display === "none" || details.style.display === "") {
        details.style.display = "block";
        icon.classList.add("rotate");
    } else {
        details.style.display = "none";
        icon.classList.remove("rotate");
    }
}
