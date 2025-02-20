document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ interview_calendar.js loaded!");

    if (typeof FullCalendar === "undefined") {
        console.error("❌ ERROR: FullCalendar failed to load!");
        return;
    }

    var calendarEl = document.getElementById('calendar');

    if (!calendarEl) {
        console.error("❌ ERROR: Calendar div not found in DOM!");
        return;
    }

    console.log("✅ Calendar div found. Initializing FullCalendar...");

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/api/get_interviews/',  // Ensure this API returns JSON
        eventColor: '#595F39',
        eventClick: function(info) {
            window.location.href = info.event.url;
        }
    });

    calendar.render();
});
