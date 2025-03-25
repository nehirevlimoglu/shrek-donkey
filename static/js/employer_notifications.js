document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".read-btn").forEach(button => {
        button.addEventListener("click", function () {
            const notificationId = this.getAttribute("data-notification-id");
            if (notificationId) {
                markAsRead(notificationId, this);
            }
        });
    });
});

function markAsRead(notificationId, button) {
    fetch(`/mark-notification-read/${notificationId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const card = document.getElementById(`notification-${notificationId}`);
            if (card) {
                card.classList.remove("unread");
                const seenText = document.createElement("span");
                seenText.textContent = "✔ Seen";
                seenText.classList.add("seen-text");
                button.replaceWith(seenText);
            }
        } else {
            console.error("Failed to mark as read:", data.error);
        }
    })
    .catch(err => console.error("Request error:", err));
}

function getCSRFToken() {
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}
