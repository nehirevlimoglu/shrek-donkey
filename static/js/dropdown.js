/**
 * Dropdown menu functionality for the admin dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the profile container and dropdown menu
    const userProfile = document.getElementById('userProfile');
    const welcomeHeader = document.getElementById('welcomeHeader');
    const dropdownMenu = document.getElementById('dropdownMenu');
    
    if (userProfile && welcomeHeader && dropdownMenu) {
        // Toggle dropdown menu when clicking on the welcome header
        welcomeHeader.addEventListener('click', function(e) {
            e.preventDefault();
            dropdownMenu.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userProfile.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    }
});
