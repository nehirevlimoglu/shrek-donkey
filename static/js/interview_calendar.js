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

