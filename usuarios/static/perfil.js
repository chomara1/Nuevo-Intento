(function() {
  'use strict';

  const profileCard = document.getElementById('profileCard');
  const toastContainer = document.getElementById('toastContainer');

  const userNameElement = document.getElementById('django-username');
  const userEmailElement = document.getElementById('django-email');

  const djangoUser = userNameElement ? userNameElement.textContent.trim() : '';
  const djangoEmail = userEmailElement ? userEmailElement.textContent.trim() : '';
  const djangoIsAuth = djangoUser !== '';

  const URLS = window.NEBULA_URLS || {
    login: '/login/',
    tiendaHome: '/',
    misEnvios: '/rastreo/mis-envios/',
  };

  function getToken() {
    return localStorage.getItem('nebula_token') || (djangoIsAuth ? 'django_session' : null);
  }

  function getUserName() {
    if (djangoIsAuth && djangoUser) return djangoUser;
    return localStorage.getItem('nebula_user') || 'Usuario';
  }

  function getUserEmail() {
    if (djangoIsAuth && djangoEmail) return djangoEmail;
    const name = getUserName();
    return name.toLowerCase().replace(/\s/g, '.') + '@nebula.com';
  }

  function isLoggedIn() {
    return !!getToken();
  }

  function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      if (toast.parentNode) toast.remove();
    }, 2800);
  }

  function logout() {
    localStorage.removeItem('nebula_token');
    localStorage.removeItem('nebula_user');
    showToast('Sesión cerrada');
    setTimeout(() => {
      window.location.href = URLS.login;
    }, 600);
  }

  function renderProfile() {
    if (!isLoggedIn()) {
      profileCard.innerHTML = `
        <div style="text-align:center; padding:2rem 0;">
          <h2 style="color:var(--purple-700);">No has iniciado sesión</h2>
          <p style="color:var(--purple-50); margin:0.8rem 0; color: var(--purple-700)">Por favor, inicia sesión para ver tu perfil.</p>
          <button id="goToLogin" class="option-card" style="display:inline-flex; justify-content:center; padding:0.8rem 2rem; margin:1rem auto 0; max-width:200px;">
            Iniciar sesión
          </button>
        </div>
      `;

      document.getElementById('goToLogin')?.addEventListener('click', () => {
        window.location.href = URLS.login;
      });
      return;
    }

    const name = getUserName();
    const email = getUserEmail();
    const initial = name.charAt(0).toUpperCase();
    const memberSince = 'Julio 2026';

    profileCard.innerHTML = `
      <div class="profile-header">
        <div class="profile-avatar">${initial}</div>
        <div class="profile-info">
          <h1>${name}</h1>
          <div class="email">${email}</div>
          <div class="member-since">Miembro desde ${memberSince}</div>
        </div>
      </div>

      <hr class="profile-divider" />

      <div class="profile-options">
        <div class="option-card" id="myOrders">
          <span class="icon">📦</span> Mis pedidos
        </div>
        <div class="option-card" id="myFavorites">
          <span class="icon">❤️</span> Mis favoritos
        </div>
        <div class="option-card logout" id="logoutBtn">
          <span class="icon">🚪</span> Cerrar sesión
        </div>
      </div>
    `;

    document.getElementById('myOrders')?.addEventListener('click', () => {
      window.location.href = URLS.misEnvios;
    });
    document.getElementById('myFavorites')?.addEventListener('click', () => {
      window.location.href = URLS.tiendaHome + '?ver=favoritos';
    });
    document.getElementById('logoutBtn')?.addEventListener('click', logout);
  }

  renderProfile();

})();