document.addEventListener('DOMContentLoaded', function() {
    const tabLinks = document.querySelectorAll('.list-group-item-action');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // The default link behavior (URL parameter) will handle the tab switching
            // This is just a hook for potential future enhancements
        });
    });
}); 