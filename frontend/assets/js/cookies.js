document.addEventListener("DOMContentLoaded", function () {
    // Nombre de la key en localStorage
    const consentKey = "plasise_cookies_accepted";

    // Si ya existe la cookie, no hacemos nada
    if (localStorage.getItem(consentKey)) {
        return;
    }

    // Crear el contenedor del banner
    const banner = document.createElement("div");
    banner.id = "cookieConsentBanner";
    banner.className = "cookie-banner";

    // Crear el contenido
    const content = document.createElement("div");
    content.className = "cookie-content";

    const title = document.createElement("strong");
    title.textContent = "Uso de Cookies";
    content.appendChild(title);

    const p = document.createElement("p");
    p.textContent = "Utilizamos cookies propias y de terceros para mejorar nuestros servicios y mostrarle publicidad relacionada con sus preferencias mediante el análisis de sus hábitos de navegación. Si continúa navegando, consideramos que acepta su uso. Puede cambiar la configuración u obtener más información en nuestra ";

    const link = document.createElement("a");
    link.href = "legales/politica-cookies.html";
    link.textContent = "Política de Cookies";

    p.appendChild(link);
    p.appendChild(document.createTextNode("."));
    content.appendChild(p);

    // Crear las acciones
    const actions = document.createElement("div");
    actions.className = "cookie-actions";

    const acceptBtn = document.createElement("button");
    acceptBtn.id = "acceptCookiesBtn";
    acceptBtn.className = "btn btn-primary";
    acceptBtn.textContent = "Aceptar y Cerrar";
    actions.appendChild(acceptBtn);

    // Armar el banner
    banner.appendChild(content);
    banner.appendChild(actions);

    // Inyectar al body
    document.body.appendChild(banner);

    // Mostrar el banner (animación)
    setTimeout(() => {
        banner.classList.add("show");
    }, 500);

    // Lógica para aceptar
    acceptBtn.addEventListener("click", function () {
        // Guardar preferencia
        localStorage.setItem(consentKey, "true");
        // Ocultar banner
        banner.classList.remove("show");
        // Eliminar del DOM tras animación
        setTimeout(() => {
            banner.remove();
        }, 400);
    });
});
