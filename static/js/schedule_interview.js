// schedule_interview.js

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const dateInput = document.getElementById("interview_date");
    const timeInput = document.getElementById("interview_time");

    form.addEventListener("submit", (e) => {
        const selectedDate = new Date(`${dateInput.value}T${timeInput.value}`);
        const now = new Date();

        if (selectedDate < now) {
            alert("Interview date and time must be in the future.");
            e.preventDefault();
        }
    });
});
