const confirmModal = document.getElementById('confirmModal');
const confirmCancelBtn = document.getElementById('confirmCancelBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
let planToDelete = null;

document.querySelectorAll('.delete-btn').forEach((button) => {
    button.addEventListener('click', () => {
        planToDelete = button.dataset.planId;
        confirmModal.classList.add('visible');
    });
});

confirmCancelBtn.addEventListener('click', () => {
    planToDelete = null;
    confirmModal.classList.remove('visible');
});

confirmDeleteBtn.addEventListener('click', async () => {
    if (!planToDelete) return;

    const response = await fetch(`/api/plans/${planToDelete}`, { method: 'DELETE' });
    if (!response.ok) {
        alert('Could not delete this plan.');
        return;
    }
    document.getElementById(`plan-card-${planToDelete}`)?.remove();
    confirmModal.classList.remove('visible');
    planToDelete = null;
});

document.querySelectorAll('.edit-btn').forEach((button) => {
    button.addEventListener('click', async () => {
        const card = button.closest('.plan-card');
        const planId = button.dataset.planId;
        const destination = prompt('Destination', card.querySelector('.plan-destination').textContent.replace('Trip to ', '').trim());
        if (destination === null) return;
        const currentLocation = prompt('Current location', card.querySelector('.plan-location').textContent.trim());
        if (currentLocation === null) return;
        const date = prompt('Date', card.querySelector('.plan-date').textContent.trim());
        if (date === null) return;
        const budget = prompt('Budget', card.querySelector('.plan-budget').textContent.trim());
        if (budget === null) return;

        const response = await fetch(`/api/plans/${planId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                destination,
                current_location: currentLocation,
                date,
                budget,
            }),
        });

        if (!response.ok) {
            alert('Could not update this plan.');
            return;
        }
        window.location.reload();
    });
});
