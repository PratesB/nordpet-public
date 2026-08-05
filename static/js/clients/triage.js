document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector('form');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (form && submitBtn) {
        form.addEventListener('submit', function(e) {
            // Check if the form is valid before changing the button state
            if (form.checkValidity()) {
                // Lock the button natively using HTML property
                submitBtn.disabled = true;
                
                // Load the HTML content from the template instead of hardcoding strings
                const template = document.getElementById('triage-loading-template');
                if (template) {
                    submitBtn.innerHTML = ''; // Clear current content
                    submitBtn.appendChild(template.content.cloneNode(true));
                }
            }
        });
    }
});
