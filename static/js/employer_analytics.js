document.addEventListener("DOMContentLoaded", function () {
    const ctx1 = document.getElementById('applicantsChart').getContext('2d');
    const applicantsChart = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: JSON.parse(document.getElementById('applicantsChart').dataset.labels),
            datasets: [{
                label: 'Applicants Per Job',
                data: JSON.parse(document.getElementById('applicantsChart').dataset.data),
                backgroundColor: ['#1A73E8', '#34A853', '#FBBC05'],
                borderRadius: 5
            }]
        },
    });

    const ctx2 = document.getElementById('acceptanceChart').getContext('2d');
    const acceptanceChart = new Chart(ctx2, {
        type: 'pie',
        data: {
            labels: ['Accepted', 'Declined'],
            datasets: [{
                label: 'Offer Acceptance Rate',
                data: JSON.parse(document.getElementById('acceptanceChart').dataset.data),
                backgroundColor: ['#34A853', '#EA4335']
            }]
        },
    });
});
