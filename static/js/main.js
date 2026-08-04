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

// Dashboard Filters
function filterAppointments(filterType) {
    const buttons = ['all', 'triaged', 'pending'];
    buttons.forEach(type => {
        const btn = document.getElementById(`btn-filter-${type}`);
        if (!btn) return;
        btn.dataset.state = (type === filterType) ? 'active' : 'inactive';
    });

    const cards = document.querySelectorAll('.appointment-card');
    cards.forEach(card => {
        if (filterType === 'all') {
            card.style.display = 'flex';
        } else if (filterType === 'triaged') {
            card.style.display = (card.dataset.triage === 'true') ? 'flex' : 'none';
        } else if (filterType === 'pending') {
            card.style.display = (card.dataset.triage === 'false') ? 'flex' : 'none';
        }
    });
}
