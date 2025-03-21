document.addEventListener("DOMContentLoaded", function () {
    let searchInput = document.getElementById("job-search");
    let dropdownResults = document.querySelector(".dropdown-results");
    let selectElement = document.getElementById("id_job_preferences");

    searchInput.addEventListener("input", function () {
        let searchTerm = searchInput.value.toLowerCase();
        dropdownResults.innerHTML = "";
        if (searchTerm.length > 0) {
            let options = Array.from(selectElement.options);
            let filteredOptions = options.filter(option =>
                option.text.toLowerCase().includes(searchTerm)
            );

            filteredOptions.forEach(option => {
                let div = document.createElement("div");
                div.textContent = option.text;
                div.setAttribute("data-value", option.value);
                div.addEventListener("click", function () {
                    let selectedOption = document.createElement("option");
                    selectedOption.value = option.value;
                    selectedOption.textContent = option.text;
                    selectedOption.selected = true;
                    selectElement.appendChild(selectedOption);
                    searchInput.value = "";
                    dropdownResults.innerHTML = "";
                });
                dropdownResults.appendChild(div);
            });

            dropdownResults.style.display = "block";
        } else {
            dropdownResults.style.display = "none";
        }
    });

    document.addEventListener("click", function (event) {
        if (!searchInput.contains(event.target) && !dropdownResults.contains(event.target)) {
            dropdownResults.style.display = "none";
        }
    });
});