const destinationsContainer = document.getElementById('destinations-container');
const addDestinationBtn = document.querySelector('.add-destination-btn');
const addPlanBtn = document.querySelector('.add-plan-btn');
const spotSearchBtn = document.querySelector('.spot-search-btn');
const firstDestinationInput = document.getElementById('first-destination-input');

function makeDestinationInput(index) {
    const wrapper = document.createElement('div');
    wrapper.className = 'destination-input-wrapper';
    wrapper.innerHTML = `
        <div class="input-group">
            <i class="fa-solid fa-map-pin"></i>
            <input type="text" class="destination-input" placeholder="Destination ${index}">
        </div>
        <button type="button" class="remove-destination-btn" title="Remove destination">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;
    wrapper.querySelector('.remove-destination-btn').addEventListener('click', () => wrapper.remove());
    return wrapper;
}

addDestinationBtn.addEventListener('click', () => {
    const count = document.querySelectorAll('.destination-input').length + 1;
    destinationsContainer.appendChild(makeDestinationInput(count));
});

addPlanBtn.addEventListener('click', async () => {
    const destinations = [...document.querySelectorAll('.destination-input')]
        .map((input) => input.value.trim())
        .filter(Boolean);

    const payload = {
        current_location: document.getElementById('current-location').value.trim(),
        destinations,
        date: document.getElementById('trip-date').value,
        budget: document.getElementById('trip-budget').value.trim(),
    };

    const response = await fetch('/api/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok) {
        alert(result.error || 'Could not save the plan.');
        return;
    }

    alert('Plan saved successfully.');
    window.location.href = '/my_plans';
});

spotSearchBtn.addEventListener('click', () => {
    const destination = firstDestinationInput.value.trim();
    window.location.href = destination ? `/search_spots?destination=${encodeURIComponent(destination)}` : '/search_spots';
});
