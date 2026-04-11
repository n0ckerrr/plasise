#!/bin/bash
echo "🚀 Actualizando Frontend de PLASISE (Responsive Fix)..."
cd /etc/easypanel/projects/n0cker/plasise/code/ || { echo "Directorio no encontrado. Saliendo."; exit 1; }

cat > fix_responsive.py << 'EOF'
import os

files_to_patch = [
    "frontend/index.html",
    "frontend/pages/index.html",
    "index_2.html"
]

patch_main = """
/* Responsive patches by script */
@media (max-width: 992px) {
    .site-header { position: relative !important; }
    .hero { padding: 60px 20px !important; }
    .hero h1 { font-size: 2.2rem !important; margin-top: 15px !important; line-height: 1.2 !important; }
    .header-actions { flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
    .login-btn { padding: 8px 12px !important; font-size: 13px !important; }
    .cart-btn { padding: 8px !important; }
    .categories-grid { display: flex !important; flex-direction: column !important; gap: 16px !important; }
    .footer-grid { display: flex !important; flex-direction: column !important; gap: 20px !important; }
    .hero-content { margin-top: 20px; }
    body { padding-bottom: 80px; }
}
"""

notif_file = "frontend/pages/admin/notificaciones.html"
patch_notif = """
    /* Notif Responsive Patch */
    @media (max-width: 992px) {
      .main { margin-left: 0; width: 100vw; height: 100vh; overflow-y: auto;}
      .content-frame { height: calc(100vh - 70px) !important; width: 100vw !important; border: none; }
      body { overflow: hidden; }
      .topbar { padding: 10px 15px !important; }
      .topbar-title { font-size: 16px !important; }
    }
"""

def apply_patch(file_path, patch):
    if not os.path.exists(file_path):
        print(f"⚠️ Saltando {file_path}, no existe en el servidor.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "/* Responsive patches by script */" in content or "/* Notif Responsive Patch */" in content:
        print(f"ℹ️ El archivo {file_path} ya estaba parcheado.")
        return
        
    new_content = content.replace("</style>", patch + "\n</style>")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Parcheado: {file_path}")

for f in files_to_patch:
    apply_patch(f, patch_main)

apply_patch(notif_file, patch_notif)
EOF

python3 fix_responsive.py
rm fix_responsive.py

echo "🎉 Frontend actualizado correctamente en el servidor!"
