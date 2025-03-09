document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: function(info, successCallback, failureCallback) {
            // Dynamically fetch interview events
            fetch('/get-interview-events/')
                .then(response => response.json())
                .then(data => {
                    // Pass the fetched data to the calendar
                    successCallback(data);
                    
                    // Highlight days with interviews after the events are loaded
                    data.forEach(event => {
                        var date = event.date;  // Assuming `date` is in 'YYYY-MM-DD' format
                        var dayCell = calendarEl.querySelector(`.fc-day[data-date="${date}"]`);
                        if (dayCell) {
                            // Highlight the day cell (you can adjust the styling here)
                            dayCell.classList.add('highlight-interview');
                        }
                    });
                })
                .catch(error => failureCallback(error));  // Handle fetch errors
        },
        eventColor: '#28A745', // Optional: Customize event color (green for interviews)
        eventTextColor: '#ffffff', // Optional: Customize event text color
    });
    calendar.render();
});
