document.addEventListener('DOMContentLoaded', function () {
    const dropdown = document.querySelector('.user-profile');
    const dropdownMenu = document.getElementById('dropdownMenu');

    dropdown.addEventListener('click', function () {
        dropdownMenu.classList.toggle('show');
    });

    // Close the dropdown menu if clicked outside
    document.addEventListener('click', function (event) {
        if (!dropdown.contains(event.target)) {
            dropdownMenu.classList.remove('show');
        }
    });
});
