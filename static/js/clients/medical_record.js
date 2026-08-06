document.addEventListener("DOMContentLoaded", function() {
    const timerElement = document.getElementById('consultation-timer');
    if (timerElement) {
        const startStr = timerElement.getAttribute('data-start');
        if (startStr) {
            const startTime = new Date(startStr).getTime();
            
            function updateTimer() {
                const now = new Date().getTime();
                const diff = now - startTime;
                
                if (diff < 0) return;
                
                const hours = Math.floor(diff / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                
                const formatted = 
                    String(hours).padStart(2, '0') + ':' + 
                    String(minutes).padStart(2, '0') + ':' + 
                    String(seconds).padStart(2, '0');
                    
                timerElement.innerText = formatted;
            }
            
            updateTimer();
            setInterval(updateTimer, 1000);
        }
    }

    // AI Summary Polling
    const pendingSummaries = document.querySelectorAll('.ai-summary-pending');
    if (pendingSummaries.length > 0) {
        pendingSummaries.forEach(function(el) {
            const recordId = el.getAttribute('data-record-id');
            const type = el.getAttribute('data-type') || 'audio'; // default to audio if not set
            if (recordId) {
                const interval = setInterval(function() {
                    fetch(`/clients/check-summary/${recordId}/`)
                        .then(response => response.json())
                        .then(data => {
                            if ((type === 'audio' && data.summary) || (type === 'exam' && data.exam_interpretation)) {
                                clearInterval(interval);
                                // The AI finished generating! Reload the page to render it.
                                window.location.reload(); 
                            }
                        })
                        .catch(error => console.error('Error fetching summary:', error));
                }, 5000); // Check every 5 seconds
            }
        });
    }
});
