// config.js - Configuración global PLASISE
// Este archivo define API_URL y funciones compartidas para todas las páginas

const API_URL = (function() {
    const host = window.location.hostname;
    // Si estamos en local o archivo, usamos el servidor de desarrollo/producción remoto conocido
    if (host === 'localhost' || host === '127.0.0.1' || window.location.protocol === 'file:') {
        return 'https://n0cker-plasise.v6hb8q.easypanel.host/api/v1';
    }
    // Si estamos en el servidor, usamos rutas relativas para evitar problemas de CORS y SSL
    if (window.location.pathname.startsWith('/plasise')) {
        return window.location.origin + '/plasise/api/v1';
    }
    return '/api/v1';
})();

// Formatear precio en EUR
function formatPrice(price) {
    if (price == null) return '';
    return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(price);
}

// Obtener URL de imagen de producto
function getImageUrl(img, productId) {
    if (!img) return 'https://via.placeholder.com/400?text=PLASISE';
    if (img.startsWith('http')) return img;
    return '/api/v1/static/images/' + img;
}

// Toast notification
function showToast(msg, type) {
    const t = document.createElement('div');
    t.textContent = msg;
    const bg = type === 'error' ? '#c0392b' : type === 'success' ? '#0b8642' : '#263238';
    t.style.cssText = 'position:fixed;right:20px;top:20px;background:' + bg + ';color:white;padding:12px 20px;border-radius:10px;z-index:12000;box-shadow:0 4px 15px rgba(0,0,0,0.15);font-size:0.9rem;transition:opacity 0.3s;';
    document.body.appendChild(t);
    setTimeout(function () { t.style.opacity = '0'; }, 2200);
    setTimeout(function () { t.remove(); }, 2800);
}

// Toggle user dropdown menu
function toggleUserMenu() {
    var menu = document.querySelector('.user-menu');
    if (menu) menu.classList.toggle('show');
}

// Close user menu when clicking outside
document.addEventListener('click', function (e) {
    var dropdown = document.getElementById('userDropdown');
    if (dropdown && !dropdown.contains(e.target)) {
        var menu = dropdown.querySelector('.user-menu');
        if (menu) menu.classList.remove('show');
    }
});

// Logout
async function logout() {
    try {
        await fetch(API_URL + '/auth/logout', { method: 'POST', credentials: 'include' });
        window.location.href = 'index.html';
    } catch (e) { console.warn('logout', e); }
}
