document.addEventListener('DOMContentLoaded', function() {
    // Retrieve CSRF token from the meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Set up click event listeners for favorite stars
    document.querySelectorAll('.favorite-star').forEach(function(star) {
        star.addEventListener('click', function() {
            const jobId = this.getAttribute('data-job-id');
            
            fetch(toggleFavoriteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ job_id: jobId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.favorited) {
                    star.innerHTML = '&#9733;'; // filled star
                } else {
                    star.innerHTML = '&#9734;'; // empty star
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});
