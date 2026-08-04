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
});
