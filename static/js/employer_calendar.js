document.addEventListener('DOMContentLoaded', function () {
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
});
