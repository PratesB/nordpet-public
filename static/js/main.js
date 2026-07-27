function updateClock() {
    const now = new Date();
    
    const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
    const timeString = now.toLocaleTimeString(undefined, timeOptions);
    
    const dateOptions = { weekday: 'short', day: '2-digit', month: 'short' };
    const dateString = now.toLocaleDateString('en-US', dateOptions);
    
    const clockTime = document.getElementById('clock-time');
    const clockDate = document.getElementById('clock-date');
    
    if (clockTime) clockTime.textContent = timeString;
    if (clockDate) clockDate.textContent = dateString;
}

setInterval(updateClock, 1000);
updateClock(); // Initial call
