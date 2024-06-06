function signUp() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Example: Log the email and password to the console
    // In a real application, you would send these details to the server
    console.log('Sign Up:', email, password);

    // Simulate account creation success
    alert('Account created successfully!');
}

function logIn() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    // Example: Log the email and password to the console
    // In a real application, you would send these details to the server
    console.log('Log In:', email, password);

    // Simulate login success
    alert('Logged in successfully!');
}

function showLoginForm() {
    document.getElementById('sign-up-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'flex';
}

function showSignUpForm() {
    document.getElementById('sign-up-form').style.display = 'flex';
    document.getElementById('login-form').style.display = 'none';
}

