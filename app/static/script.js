const openButtons = document.querySelectorAll('.open-form');
const closeButtons = document.querySelectorAll('.close-form');
const popupForms = document.querySelectorAll('.popup-form');

openButtons.forEach((button) => {
    button.addEventListener('click', () => {
        const broker = button.dataset.broker;
        const popupForm = document.getElementById(`popup-${broker}`);
        popupForm.style.display = 'block';
    });
});

closeButtons.forEach((button) => {
    button.addEventListener('click', () => {
        const popupForm = button.closest('.popup-form');
        popupForm.style.display = 'none';
    });
});

window.addEventListener('click', (event) => {
    popupForms.forEach((popupForm) => {
        if (event.target === popupForm) {
            popupForm.style.display = 'none';
        }
    });
});

const submitButtons = document.querySelectorAll('.submit-btn');
const cancelButtons = document.querySelectorAll('.cancel-btn');

// submitButtons.forEach((button) => {
//     button.addEventListener('click', () => {
//         const popupForm = button.closest('.popup-form');
//         // Perform form submission or other operations
//         popupForm.style.display = 'none'; // Hide the form after submission
//     });
// });

cancelButtons.forEach((button) => {
    button.addEventListener('click', () => {
        const popupForm = button.closest('.popup-form');
        popupForm.style.display = 'none'; // Hide the form on cancel
    });
});