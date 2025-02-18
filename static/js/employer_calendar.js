document.addEventListener('DOMContentLoaded', function () {
    let calendarEl = document.getElementById('calendar');

    if (calendarEl) {
        let calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: '/api/get_interviews/', // Fetch interview events from Django API
            eventClick: function(info) {
                alert('Interview Details:\n' + info.event.title + '\n' + info.event.start.toLocaleString());
            }
        });

        calendar.render();
    }
});
