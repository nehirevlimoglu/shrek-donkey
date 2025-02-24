const ctx = document.getElementById('activeUserChart').getContext('2d');

const data = {
    day: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        values: [120, 150, 180, 220, 260, 200, 190]
    },
    week: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        values: [700, 820, 750, 900]
    },
    month: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        values: [3000, 2800, 3200, 3500, 3400, 3600, 3700, 3900, 3800, 4000, 4200, 4500]
    }
};

let currentPeriod = 'day';

let activeUserChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: data[currentPeriod].labels,
        datasets: [{
            label: 'Active Users',
            data: data[currentPeriod].values,
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
                }
            }
        }
    }
});

function updateChart(period) {
    currentPeriod = period;
    activeUserChart.data.labels = data[period].labels;
    activeUserChart.data.datasets[0].data = data[period].values;
    activeUserChart.update();
}

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
        updateChart(this.dataset.period);
    });
});

document.querySelector('.filter-btn[data-period="day"]').classList.add('active');
