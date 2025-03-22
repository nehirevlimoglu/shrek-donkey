// Add functionality to view job details
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.view-btn').forEach(button => {
        button.addEventListener('click', function() {
            const jobId = this.getAttribute('data-job-id');
            // Navigate to job detail page
            window.location.href = `/admin_job_detail/${jobId}/`;
        });
    });

    
    const tableContainer = document.querySelector('.table-container');
    if (tableContainer) {
        
        tableContainer.scrollTop = 0;
    }

   
    const currentUrl = window.location.search;
    const tabLinks = document.querySelectorAll('.tab');
    tabLinks.forEach(tab => {
        const tabUrl = tab.getAttribute('href');
        if (currentUrl.includes(tabUrl) || (currentUrl === '' && tabUrl.includes('status=all'))) {
            tab.classList.add('active');
        }
    });
}); 