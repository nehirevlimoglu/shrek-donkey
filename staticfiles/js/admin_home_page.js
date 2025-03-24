document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('activeUserChart').getContext('2d');
    let activeUserChart;
    let currentPeriod = 'day';

    // Initialize chart
    function initChart(data) {
        activeUserChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Active Users',
                    data: data.values,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#333'
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time Period',
                            color: '#333'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Active Users',
                            color: '#333'
                        },
                        beginAtZero: true,
                        min: 0,
                        ticks: {
                            precision: undefined,
                            callback: function(value) {
                                if (Math.max(...this.chart.data.datasets[0].data) < 10) {
                                    return Number(value).toFixed(1);
                                }
                                return Math.round(value);
                            }
                        }
                    }
                }
            }
        });
    }

    // Fetch data from backend
    function fetchData(period) {
        fetch(`/api/get_active_users_data/?period=${period}`)
            .then(response => response.json())
            .then(data => {
                if (activeUserChart) {
                    activeUserChart.data.labels = data.labels;
                    activeUserChart.data.datasets[0].data = data.values;
                    activeUserChart.update();
                } else {
                    initChart(data);
                }
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    // Initial load
    fetchData(currentPeriod);

    // Add button event listeners
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentPeriod = this.dataset.period;
            fetchData(currentPeriod);
        });
    });

    // Default select day button
    document.querySelector('.filter-btn[data-period="day"]').classList.add('active');
}); 