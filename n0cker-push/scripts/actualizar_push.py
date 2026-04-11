import os
import re

def replace_in_file(file_path, replacements):
    if not os.path.exists(file_path):
        print(f"Skipping: {file_path} (Not found)")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements.items():
        content = re.sub(old, new, content, flags=re.IGNORECASE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
    else:
        print(f"No changes in: {file_path}")

# Definición de reemplazos
replacements = {
    r'N0CKER': 'PLASISE',
    r'admin@n0cker\.com': 'info@plasise.com',
    # Colores
    r'#00ff41': '#c8a45e', # Neon Green -> Gold
    r'#00ffff': '#d4b76a', # Neon Cyan -> Light Gold
    r'#ff00ff': '#a6894c', # Neon Magenta -> Dark Gold
}

# Archivos a procesar
project_root = r'C:\Users\plasi\Documents\PROYECTOS\PROYECTOS-ANTIGRAVITY\code\code\n0cker-push'
files_to_process = [
    os.path.join(project_root, 'server.js'),
    os.path.join(project_root, 'README.md'),
    os.path.join(project_root, 'public', 'index.html'),
    os.path.join(project_root, 'public', 'admin.html'),
    os.path.join(project_root, 'public', 'app.js'),
    os.path.join(project_root, 'public', 'sw.js'),
    os.path.join(project_root, 'public', 'manifest.json'),
]

if __name__ == '__main__':
    for file_path in files_to_process:
        replace_in_file(file_path, replacements)
    
    print("\nProceso de actualización completado.")
