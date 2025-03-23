document.addEventListener('DOMContentLoaded', function() {
    // Retrieve CSRF token from the meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Attach click event listeners to each favorite-star element
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
                    this.innerHTML = '&#9733;'; // Filled star
                    this.classList.add("active");
                } else {
                    this.innerHTML = '&#9734;'; // Empty star
                    this.classList.remove("active");
                    // Optionally, remove the row if you want to hide unfavourited jobs
                    // this.closest('tr').remove();
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});
