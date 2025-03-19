<<<<<<< HEAD
/*document.addEventListener('DOMContentLoaded', function () {
    let calendarEl = document.getElementById('calendar');

    if (!calendarEl) {
        console.error("❌ Calendar element not found!");
        return;
    }

    let calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: interviewData, // ✅ Use Django-rendered data, no API needed
        eventClick: function(info) {
            alert('Interview Details:\n' + info.event.title + '\n' + info.event.start.toLocaleString());
        }
    });

    calendar.render();
});*/

document.addEventListener('DOMContentLoaded', function() {
  let calendarEl = document.getElementById('calendar');

  // Create the calendar instance
  let calendar = new FullCalendar.Calendar(calendarEl, {
    // Choose the default view: 'dayGridMonth', 'timeGridWeek', etc.
    initialView: 'dayGridMonth',

    // Provide the interview events you embedded in the template
    events: interviewData,

    // (Optional) Customize the header
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek'
    },

    // (Optional) Handler when user clicks an event
    eventClick: function(info) {
      alert(`Clicked on event: ${info.event.title}`);
      // You could redirect to interview detail page, etc.
    },
  });

  // Finally, render the calendar
  calendar.render();
});

=======
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
>>>>>>> dd211a8ba0e976635fdc1f13cd2c45da93ef6bb2
