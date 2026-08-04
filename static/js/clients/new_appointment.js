class SearchableDropdown {
    constructor(selectElement) {
        this.select = selectElement;
        this.options = Array.from(this.select.options);
        
        this.select.style.position = 'absolute';
        this.select.style.opacity = '0';
        this.select.style.pointerEvents = 'none';
        
        const template = document.getElementById('searchable-dropdown-template');
        if (template) {
            this.container = template.content.firstElementChild.cloneNode(true);
            this.input = this.container.querySelector('input');
            this.dropdown = this.container.querySelector('ul');
            
            this.input.placeholder = this.select.options[0] ? this.select.options[0].text : 'Search...';
            
            this.select.parentNode.insertBefore(this.container, this.select.nextSibling);
            
            const parentDiv = this.select.parentNode;
            Array.from(parentDiv.children).forEach(child => {
                if (child.tagName === 'SPAN' && child.textContent.includes('expand_more')) {
                    child.remove();
                }
            });
            
            if (parentDiv.classList.contains('relative')) {
                parentDiv.classList.remove('relative');
            }
        } else {
            console.error("Searchable dropdown template not found");
            return;
        }
        
        this.setupEventListeners();
        this.renderOptions();
        
        if (this.select.value && this.select.selectedIndex > 0) {
            this.input.value = this.select.options[this.select.selectedIndex].text;
        }
    }
    
    renderOptions(filterText = '') {
        this.dropdown.innerHTML = '';
        
        if (filterText.trim() === '') {
            const template = document.getElementById('dropdown-empty-template');
            if (template) {
                const li = template.content.firstElementChild.cloneNode(true);
                li.textContent = 'Start typing to search...';
                this.dropdown.appendChild(li);
            }
            return;
        }

        let hasVisibleOptions = false;
        
        this.options.forEach((opt, index) => {
            if (index === 0 && !opt.value) return;
            
            const rawText = opt.text;
            const name = opt.dataset.name || rawText;
            const specie = opt.dataset.specie;
            const owner = opt.dataset.owner;
            const role = opt.dataset.role;
            
            const searchString = `${name} ${specie || ''} ${owner || ''} ${role || ''}`.toLowerCase();
            
            if (searchString.includes(filterText.toLowerCase())) {
                const template = document.getElementById('dropdown-item-template');
                if (!template) return;
                
                const li = template.content.firstElementChild.cloneNode(true);
                
                const iconContainer = li.querySelector('.dropdown-icon-container');
                const icon = li.querySelector('.dropdown-icon');
                const nameSpan = li.querySelector('.dropdown-name');
                const detailsSpan = li.querySelector('.dropdown-details');
                const textContainer = li.querySelector('.dropdown-text-container');
                
                nameSpan.textContent = name;
                
                if (specie) {
                    iconContainer.dataset.type = 'animal';
                    icon.textContent = 'pets';
                    detailsSpan.innerHTML = `${specie} &bull; Owner: ${owner}`;
                } else if (role) {
                    iconContainer.dataset.type = 'vet';
                    icon.textContent = 'medical_services';
                    detailsSpan.textContent = role;
                } else {
                    iconContainer.remove();
                    detailsSpan.remove();
                    textContainer.dataset.hasDetails = 'false';
                }
                
                li.dataset.selected = (this.select.value === opt.value).toString();
                
                li.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    this.select.value = opt.value;
                    this.input.value = name;
                    this.dropdown.classList.add('hidden');
                    this.container.style.zIndex = '1';
                    this.select.dispatchEvent(new Event('change', { bubbles: true }));
                });
                
                this.dropdown.appendChild(li);
                hasVisibleOptions = true;
            }
        });
        
        if (!hasVisibleOptions) {
            const template = document.getElementById('dropdown-empty-template');
            if (template) {
                const li = template.content.firstElementChild.cloneNode(true);
                li.textContent = 'No results found';
                this.dropdown.appendChild(li);
            }
        }
    }
    
    setupEventListeners() {
        this.input.addEventListener('focus', () => {
            this.dropdown.classList.remove('hidden');
            this.container.style.zIndex = '9999';
            this.renderOptions(this.input.value);
        });
        
        this.input.addEventListener('input', (e) => {
            this.dropdown.classList.remove('hidden');
            this.container.style.zIndex = '9999';
            this.renderOptions(e.target.value);
            if (this.select.value) {
                const selectedOpt = this.options[this.select.selectedIndex];
                if (selectedOpt && selectedOpt.text !== e.target.value) {
                    this.select.value = '';
                    this.select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });
        
        this.input.addEventListener('blur', () => {
            setTimeout(() => {
                this.dropdown.classList.add('hidden');
                this.container.style.zIndex = '1';
                if (this.select.value && this.select.selectedIndex > 0) {
                    this.input.value = this.options[this.select.selectedIndex].text;
                } else {
                    this.input.value = '';
                    this.select.value = '';
                    this.select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }, 150);
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('appointment-form');
    const appointmentId = form.dataset.appointmentId;
    const vetSelect = document.getElementById('veterinarian');
    const reasonRadios = document.querySelectorAll('input[name="reason"]');
    const dateInput = document.getElementById('appointment_date');
    const timeInput = document.getElementById('appointment_time');
    const durationSelect = document.getElementById('duration');

    // Initialize searchable dropdowns
    const animalSelect = document.getElementById('animal');
    if (animalSelect) new SearchableDropdown(animalSelect);
    if (vetSelect) new SearchableDropdown(vetSelect);

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
            timeInput.disabled = true;
            
            // Force duration to 30 min and lock the select field
            durationSelect.value = '30';
            durationSelect.disabled = true;
        } else {
            // Unlock the fields
            dateInput.readOnly = false;
            timeInput.disabled = false;
            durationSelect.disabled = false;
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
