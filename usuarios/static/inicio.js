// Seleccionamos las pestañas (botones)
const loginTab = document.getElementById('logintap');
const signupTab = document.getElementById('signuptap');

// Seleccionamos los formularios
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');

// Evento al hacer clic en la pestaña de Login
if (loginTab) {
    loginTab.addEventListener('click', () => {
        // Activamos la pestaña Login y desactivamos Sign Up
        loginTab.classList.add('active');
        signupTab.classList.remove('active');
        
        // Mostramos el formulario Login y ocultamos Sign Up
        loginForm.classList.add('active');
        signupForm.classList.remove('active');
    });
}

// Evento al hacer clic en la pestaña de Sign Up
if (signupTab) {
    signupTab.addEventListener('click', () => {
        // Activamos la pestaña Sign Up y desactivamos Login
        signupTab.classList.add('active');
        loginTab.classList.remove('active');
        
        // Mostramos el formulario Sign Up y ocultamos Login
        signupForm.classList.add('active');
        loginForm.classList.remove('active');
    });
}
