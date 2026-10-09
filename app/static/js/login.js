const loginTab = document.getElementById('login-tab');
const signupTab = document.getElementById('signup-tab');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const passwordError = document.getElementById('password-error');

function showMessage(message, isError = true) {
    let messageBox = document.getElementById('form-message');
    if (!messageBox) {
        messageBox = document.createElement('p');
        messageBox.id = 'form-message';
        messageBox.className = 'error-message';
        document.getElementById('form-content').prepend(messageBox);
    }
    messageBox.textContent = message;
    messageBox.style.color = isError ? '#ef4444' : '#16a34a';
}

loginTab.addEventListener('click', () => {
    loginTab.classList.add('tab-active');
    signupTab.classList.remove('tab-active');
    loginForm.classList.remove('hidden');
    signupForm.classList.add('hidden');
});

signupTab.addEventListener('click', () => {
    signupTab.classList.add('tab-active');
    loginTab.classList.remove('tab-active');
    signupForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
});

loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
        phone: document.getElementById('login-phone').value,
        password: document.getElementById('login-password').value,
    };

    const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok) {
        showMessage(result.error || 'Login failed.');
        return;
    }
    window.location.href = result.redirect;
});

signupForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;

    if (password !== confirmPassword) {
        passwordError.classList.remove('hidden');
        return;
    }
    passwordError.classList.add('hidden');

    const payload = {
        name: document.getElementById('signup-name').value,
        surname: document.getElementById('signup-surname').value,
        email: document.getElementById('signup-email').value,
        phone: document.getElementById('signup-phone').value,
        gender: document.getElementById('signup-gender').value,
        password,
    };

    const response = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok) {
        showMessage(result.error || 'Signup failed.');
        return;
    }
    window.location.href = result.redirect;
});
