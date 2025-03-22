document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const jobForm = document.querySelector('.job-form');
    if (jobForm) {
        jobForm.addEventListener('submit', function(event) {
            // Validate form fields
            const title = document.getElementById('title').value.trim();
            const companyName = document.getElementById('company_name').value.trim();
            const location = document.getElementById('location').value.trim();
            const description = document.getElementById('description').value.trim();
            const contactEmail = document.getElementById('contact_email').value.trim();
            
            let isValid = true;
            let errorMessage = '';
            
            if (!title) {
                isValid = false;
                errorMessage += 'Job title is required.\n';
            }
            
            if (!companyName) {
                isValid = false;
                errorMessage += 'Company name is required.\n';
            }
            
            if (!location) {
                isValid = false;
                errorMessage += 'Location is required.\n';
            }
            
            if (!description) {
                isValid = false;
                errorMessage += 'Job description is required.\n';
            }
            
            if (!contactEmail) {
                isValid = false;
                errorMessage += 'Contact email is required.\n';
            } else if (!validateEmail(contactEmail)) {
                isValid = false;
                errorMessage += 'Please enter a valid email address.\n';
            }
            
            // Check application deadline is in the future
            const deadlineInput = document.getElementById('application_deadline');
            if (deadlineInput && deadlineInput.value) {
                const deadline = new Date(deadlineInput.value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                
                if (deadline < today) {
                    isValid = false;
                    errorMessage += 'Application deadline must be a future date.\n';
                }
            }
            
            if (!isValid) {
                event.preventDefault();
                alert('Please correct the following errors:\n' + errorMessage);
            }
        });
    }
    
    // Character counter for description and requirements
    setupCharacterCounter('description', 2000);
    setupCharacterCounter('requirements', 1000);
    setupCharacterCounter('benefits', 500);
});

function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function setupCharacterCounter(elementId, maxChars) {
    const textarea = document.getElementById(elementId);
    if (!textarea) return;
    
    // Create counter element
    const counter = document.createElement('div');
    counter.className = 'char-counter';
    counter.innerHTML = `0/${maxChars}`;
    textarea.parentNode.appendChild(counter);
    
    // Update counter
    function updateCounter() {
        const count = textarea.value.length;
        counter.innerHTML = `${count}/${maxChars}`;
        
        if (count > maxChars) {
            counter.classList.add('char-counter-exceeded');
        } else {
            counter.classList.remove('char-counter-exceeded');
        }
    }
    
    // Initial count
    updateCounter();
    
    // Add event listener
    textarea.addEventListener('input', updateCounter);
} 