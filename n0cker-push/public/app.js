// Verificar si el navegador soporta notificaciones
if (!('Notification' in window)) {
  showMessage('Tu navegador no soporta notificaciones push', 'error');
}

// Verificar si el navegador soporta Service Workers
if (!('serviceWorker' in navigator)) {
  showMessage('Tu navegador no soporta Service Workers', 'error');
}

let swRegistration = null;
let publicVapidKey = null;

// Cargar estadísticas
async function loadStats() {
  try {
    const response = await fetch('/api/stats');
    const data = await response.json();
    document.getElementById('totalSubs').textContent = data.totalSubscribers;
  } catch (error) {
    console.error('Error cargando estadísticas:', error);
  }
}

// Mostrar mensajes al usuario
function showMessage(message, type = 'info') {
  const messageDiv = document.getElementById('message');
  const className = type === 'error' ? 'error' : type === 'warning' ? 'warning' : '';
  messageDiv.innerHTML = `<div class="info-box ${className}">${message}</div>`;
}

// Registrar Service Worker
async function registerServiceWorker() {
  try {
    swRegistration = await navigator.serviceWorker.register('/sw.js');
    console.log('Service Worker registrado:', swRegistration);
    return swRegistration;
  } catch (error) {
    console.error('Error registrando Service Worker:', error);
    showMessage('Error al registrar el Service Worker', 'error');
  }
}

// Obtener la clave pública VAPID
async function getPublicKey() {
  try {
    const response = await fetch('/api/vapidPublicKey');
    const data = await response.json();
    return data.publicKey;
  } catch (error) {
    console.error('Error obteniendo clave pública:', error);
    return null;
  }
}

// Convertir clave VAPID de base64 a Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');
  
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Suscribirse a notificaciones push
async function subscribeToPush() {
  try {
    if (!swRegistration) {
      swRegistration = await registerServiceWorker();
    }
    
    if (!publicVapidKey) {
      publicVapidKey = await getPublicKey();
    }
    
    if (!publicVapidKey) {
      showMessage('No se pudo obtener la clave de suscripción', 'error');
      return;
    }
    
    const subscription = await swRegistration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicVapidKey)
    });
    
    // Enviar la suscripción al servidor
    const response = await fetch('/api/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(subscription)
    });
    
    if (response.ok) {
      showMessage('✓ Notificaciones activadas correctamente', 'info');
      updateButtonState(true);
      loadStats();
    } else {
      showMessage('Error al suscribirse a notificaciones', 'error');
    }
  } catch (error) {
    console.error('Error en la suscripción:', error);
    if (error.name === 'NotAllowedError') {
      showMessage('Has bloqueado las notificaciones. Por favor, habilítalas en la configuración de tu navegador.', 'warning');
    } else {
      showMessage('Error al activar notificaciones: ' + error.message, 'error');
    }
  }
}

// Desuscribirse de notificaciones push
async function unsubscribeFromPush() {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      await subscription.unsubscribe();
      
      // Notificar al servidor
      await fetch('/api/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ endpoint: subscription.endpoint })
      });
      
      showMessage('✓ Notificaciones desactivadas', 'info');
      updateButtonState(false);
      loadStats();
    }
  } catch (error) {
    console.error('Error al desuscribirse:', error);
    showMessage('Error al desactivar notificaciones', 'error');
  }
}

// Actualizar estado de los botones
function updateButtonState(subscribed) {
  const enableBtn = document.getElementById('enableBtn');
  const disableBtn = document.getElementById('disableBtn');
  
  if (subscribed) {
    enableBtn.style.display = 'none';
    disableBtn.style.display = 'inline-block';
  } else {
    enableBtn.style.display = 'inline-block';
    disableBtn.style.display = 'none';
  }
}

// Verificar si ya está suscrito
async function checkSubscription() {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    updateButtonState(!!subscription);
    
    if (subscription) {
      showMessage('Ya estás suscrito a las notificaciones', 'info');
    }
  } catch (error) {
    console.error('Error verificando suscripción:', error);
  }
}

// Solicitar permisos de notificación
async function requestNotificationPermission() {
  const permission = await Notification.requestPermission();
  if (permission === 'granted') {
    subscribeToPush();
  } else if (permission === 'denied') {
    showMessage('Has denegado los permisos de notificación', 'error');
  }
}

// Event listeners
document.getElementById('enableBtn').addEventListener('click', () => {
  requestNotificationPermission();
});

document.getElementById('disableBtn').addEventListener('click', () => {
  unsubscribeFromPush();
});

// Inicialización
(async () => {
  await registerServiceWorker();
  await checkSubscription();
  await loadStats();
  
  // Actualizar estadísticas cada 10 segundos
  setInterval(loadStats, 10000);
})();
