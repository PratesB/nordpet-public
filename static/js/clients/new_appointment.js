document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('appointment-form');
    const appointmentId = form.dataset.appointmentId;
    const vetSelect = document.getElementById('veterinarian');
    const reasonRadios = document.querySelectorAll('input[name="reason"]');
    const dateInput = document.getElementById('appointment_date');
    const timeInput = document.getElementById('appointment_time');
    const durationSelect = document.getElementById('duration');

    async function fetchAvailableTimes() {
        const vetId = vetSelect.value;
        const dateStr = dateInput.value;
        
        if (!vetId || !dateStr) return;
        
        try {
            let url = `/clients/api/available-times/?vet_id=${vetId}&date=${dateStr}`;
            if (appointmentId) {
                url += `&appointment_id=${appointmentId}`;
            }
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            
            // Backup the currently selected time (if any)
            const currentTime = timeInput.value;
            
            // Clear existing options
            timeInput.innerHTML = '<option value="" disabled selected>Select Time...</option>';
            
            data.available_times.forEach(slot => {
                const option = new Option(slot, slot);
                timeInput.add(option);
            });
            
            // Restore selection if it's still available
            if (currentTime && Array.from(timeInput.options).some(opt => opt.value === currentTime)) {
                timeInput.value = currentTime;
            }
            
            // Re-run emergency lock if emergency is currently selected
            handleEmergency();
            
        } catch (error) {
            console.error("Failed to fetch available times:", error);
        }
    }

    function handleEmergency() {
        const selectedReason = document.querySelector('input[name="reason"]:checked');
        if (selectedReason && selectedReason.value === 'emergency') {
            // Format local datetime
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            
            dateInput.value = `${year}-${month}-${day}`;
            
            const timeValue = `${hours}:${minutes}`;
            // If the exact time is not in the select, add it
            if (!Array.from(timeInput.options).some(opt => opt.value === timeValue)) {
                timeInput.add(new Option(timeValue, timeValue));
            }
            timeInput.value = timeValue;
            
            // Lock the date and time fields
            dateInput.readOnly = true;
            dateInput.classList.add('bg-surface-variant', 'opacity-70', 'cursor-not-allowed', 'pointer-events-none');
            timeInput.classList.add('bg-surface-variant', 'opacity-70', 'cursor-not-allowed', 'pointer-events-none');
            
            // Force duration to 30 min and lock the select field
            durationSelect.value = '30';
            durationSelect.classList.add('bg-surface-variant', 'opacity-70', 'cursor-not-allowed', 'pointer-events-none');
        } else {
            // Unlock the fields
            dateInput.readOnly = false;
            dateInput.classList.remove('bg-surface-variant', 'opacity-70', 'cursor-not-allowed', 'pointer-events-none');
            timeInput.classList.remove('bg-surface-variant', 'opacity-70', 'cursor-not-allowed', 'pointer-events-none');
            durationSelect.classList.remove('bg-surface-variant', 'opacity-70', 'cursor-not-allowed', 'pointer-events-none');
        }
    }

    // Event listeners
    if (vetSelect) vetSelect.addEventListener('change', fetchAvailableTimes);
    if (dateInput) dateInput.addEventListener('change', fetchAvailableTimes);
    reasonRadios.forEach(radio => radio.addEventListener('change', handleEmergency));

    // Initial run
    handleEmergency();
    fetchAvailableTimes();
});
