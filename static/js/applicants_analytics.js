<script>
    const applicationsChart = new Chart(document.getElementById('applicationsChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Applications Submitted',
                data: {{ applications_over_time|safe }},
                borderColor: '#1A73E8',
                fill: false
            }]
        }
    });

    const offerChart = new Chart(document.getElementById('offerChart').getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Accepted', 'Declined'],
            datasets: [{
                data: {{ offer_acceptance_breakdown|safe }},
                backgroundColor: ['#34A853', '#EA4335']
            }]
        }
    });
</script>
