document.addEventListener('DOMContentLoaded', function() {
    const userProfile = document.getElementById('userProfile');
    const dropdownMenu = document.getElementById('dropdownMenu');

    if (userProfile && dropdownMenu) {
        userProfile.addEventListener('click', function(event) {
            event.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        window.addEventListener('click', function(event) {
            if (!userProfile.contains(event.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    }
});
