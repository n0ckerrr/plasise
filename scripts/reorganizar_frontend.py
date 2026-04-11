"""
reorganizar_frontend.py – Limpieza y reorganizacion del frontend PLASISE.
Idempotente: se puede ejecutar varias veces sin dano.

Acciones:
  1. Backup completo del directorio frontend
  2. Renombrar cookies-v1.js -> cookies.js
  3. Normalizar rutas assets en todas las paginas (pages/, admin/, legales/)
  4. Anadir config.js a paginas que no lo tengan
  5. Crear index.html raiz como redirect
  6. Eliminar archivos duplicados/obsoletos
  7. Informe final
"""

import os, re, shutil, datetime

# ── Configuracion ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
FRONTEND   = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend'))
PAGES_DIR  = os.path.join(FRONTEND, 'pages')
ASSETS_DIR = os.path.join(FRONTEND, 'assets')
TMP_DIR    = os.path.normpath(os.path.join(BASE_DIR, '..', '.tmp'))
BACKUP_DIR = os.path.join(TMP_DIR, f'backup_frontend_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}')

OBSOLETE_FILES = [
    os.path.join(PAGES_DIR,  'logina.html'),
    os.path.join(PAGES_DIR,  'productos_CON_BUSCADOR.html'),
    os.path.join(FRONTEND,   'carrito.html'),
    os.path.join(FRONTEND,   'login.html'),
    os.path.join(FRONTEND,   'pedido.html'),
    os.path.join(FRONTEND,   'perfil.html'),
    os.path.join(FRONTEND,   'producto-detalle.html'),
    os.path.join(FRONTEND,   'productos.html'),
    os.path.join(FRONTEND,   'registro.html'),
    os.path.join(FRONTEND,   'sobre-nosotros.html'),
    os.path.join(FRONTEND,   'index_live.html'),
    os.path.join(ASSETS_DIR, 'css', 'premium.css'),
    os.path.join(ASSETS_DIR, 'js',  'luxe.js'),
]

# ── Log helper (ASCII-safe para Windows cp1252) ────────────────────────────────
changes = []
def log(msg):
    safe = msg.encode('ascii', errors='replace').decode('ascii')
    print(safe)
    changes.append(msg)

# ── Patch de un archivo HTML ───────────────────────────────────────────────────
def patch_html(filepath, page_depth=1):
    """
    Normaliza rutas, cambia cookies-v1.js -> cookies.js,
    y anade config.js si falta.
    page_depth=1 para /pages/, 2 para /pages/admin/ y /pages/legales/
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        original = f.read()

    content  = original
    name     = os.path.basename(filepath)
    prefix   = '../' * page_depth   # '../' o '../../'

    # Normalizar rutas relativas sin prefijo (assets/ -> prefix+assets/)
    for attr in ('href', 'src'):
        for folder in ('assets/css/', 'assets/js/', 'assets/img/'):
            bare      = f'{attr}="{folder}'
            corrected = f'{attr}="{prefix}{folder}'
            if bare in content:
                count = content.count(bare)
                content = content.replace(bare, corrected)
                log(f'  [RUTA] {name}: {bare!r} -> {corrected!r} ({count}x)')

    # cookies-v1.js -> cookies.js
    if 'cookies-v1.js' in content:
        count = content.count('cookies-v1.js')
        content = content.replace('cookies-v1.js', 'cookies.js')
        log(f'  [COOKIE] {name}: cookies-v1.js -> cookies.js ({count}x)')

    # Anadir config.js si no esta
    config_tag = f'<script src="{prefix}assets/js/config.js"></script>'
    if 'config.js' not in content and '</head>' in content.lower():
        content = re.sub(r'(</head>)', config_tag + '\n\\1', content, count=1, flags=re.IGNORECASE)
        log(f'  [CONFIG] {name}: anadido config.js')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# ═══════════════════════════════════════════════════════════════════════════════
log('=' * 60)
log('REORGANIZACION FRONTEND PLASISE')
log('=' * 60)

# 1. BACKUP
log('\n[1/6] Creando backup...')
os.makedirs(TMP_DIR, exist_ok=True)
shutil.copytree(FRONTEND, BACKUP_DIR)
log(f'  [OK] Backup en: {BACKUP_DIR}')

# 2. RENOMBRAR cookies-v1.js -> cookies.js
log('\n[2/6] Renombrando cookies-v1.js -> cookies.js...')
old_f = os.path.join(ASSETS_DIR, 'js', 'cookies-v1.js')
new_f = os.path.join(ASSETS_DIR, 'js', 'cookies.js')
if os.path.exists(old_f):
    shutil.copy2(old_f, new_f)
    os.remove(old_f)
    log('  [OK] Renombrado: cookies-v1.js -> cookies.js')
else:
    log('  [--] cookies-v1.js no encontrado (ya procesado?)')

# 3. NORMALIZAR PAGINAS /pages/
log('\n[3/6] Normalizando paginas en /pages/...')
for fname in sorted(os.listdir(PAGES_DIR)):
    if fname.endswith('.html'):
        changed = patch_html(os.path.join(PAGES_DIR, fname), page_depth=1)
        if not changed:
            log(f'  [--] {fname}: sin cambios')

for subfolder, depth in [('admin', 2), ('legales', 2)]:
    sub_dir = os.path.join(PAGES_DIR, subfolder)
    if os.path.isdir(sub_dir):
        log(f'\n  [{subfolder.upper()}]')
        for fname in sorted(os.listdir(sub_dir)):
            if fname.endswith('.html'):
                changed = patch_html(os.path.join(sub_dir, fname), page_depth=depth)
                if not changed:
                    log(f'  [--] {subfolder}/{fname}: sin cambios')

# 4. CREAR INDEX.HTML RAIZ (redirect)
log('\n[4/6] Creando index.html raiz con redirect...')
root_index = os.path.join(FRONTEND, 'index.html')
redirect_html = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=pages/index.html">
  <title>PLASISE</title>
  <script>window.location.replace('pages/index.html');</script>
</head>
<body><p>Redirigiendo... <a href="pages/index.html">Clic aqui</a></p></body>
</html>"""
with open(root_index, 'w', encoding='utf-8') as f:
    f.write(redirect_html)
log('  [OK] index.html raiz creado (redirect a pages/index.html)')

# 5. ELIMINAR OBSOLETOS
log('\n[5/6] Eliminando archivos obsoletos...')
eliminated = 0
for filepath in OBSOLETE_FILES:
    if os.path.exists(filepath):
        os.remove(filepath)
        log(f'  [DEL] {os.path.relpath(filepath, FRONTEND)}')
        eliminated += 1
    else:
        log(f'  [--] No existe: {os.path.relpath(filepath, FRONTEND)}')

# 6. INFORME FINAL
log('\n[6/6] Estructura resultante:')
for root, dirs, files in os.walk(FRONTEND):
    dirs[:] = sorted([d for d in dirs
                      if not d.startswith('.')
                      and d not in ('products', 'product_images')])
    rel   = os.path.relpath(root, FRONTEND)
    depth = rel.count(os.sep) if rel != '.' else 0
    ind   = '  ' * depth
    label = os.path.basename(root) if rel != '.' else 'frontend/'
    print(f'{ind}[DIR] {label}/')
    for fname in sorted(files):
        fsize = os.path.getsize(os.path.join(root, fname))
        print(f'{ind}  {fname} ({fsize // 1024}KB)')

log(f'\n[DONE] Archivos eliminados: {eliminated}')
log(f'       Backup disponible en: {BACKUP_DIR}')

# Guardar log
os.makedirs(TMP_DIR, exist_ok=True)
log_path = os.path.join(TMP_DIR, 'reorganizacion_log.txt')
with open(log_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(changes))
print(f'\nLog guardado: {log_path}')
