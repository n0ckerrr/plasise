import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

def fix_admin_link():
    html_files = glob.glob(os.path.join(FRONTEND_DIR, '**', '*.html'), recursive=True)
    count = 0
    for file in html_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # We need to replace class="d-none" on the adminLink with style="display: none;"
        # This bypasses the !important issue with Bootstrap's d-none
        if 'id="adminLink"' in content and 'd-none' in content:
            # various forms
            content = content.replace('id="adminLink" class="d-none"', 'id="adminLink" style="display: none;"')
            content = content.replace('class="d-none" href="admin/productos.html" id="adminLink"', 'style="display: none;" href="admin/productos.html" id="adminLink"')
            content = content.replace('id="adminLink" class="d-none d-flex"', 'id="adminLink" style="display: none;"')
            
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
    print(f"Fixed adminLink in {count} HTML files.")

def fix_iframe_redirect():
    notif_file = os.path.join(FRONTEND_DIR, 'pages', 'admin', 'notificaciones.html')
    if os.path.exists(notif_file):
        with open(notif_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add sandbox attribute to prevent top-level redirect framebusting
        if 'id="pushFrame"' in content and 'sandbox=' not in content:
            content = content.replace(
                '<iframe id="pushFrame" class="content-frame" title="Push Admin Panel"></iframe>',
                '<iframe id="pushFrame" class="content-frame" title="Push Admin Panel" sandbox="allow-scripts allow-forms allow-same-origin allow-popups"></iframe>'
            )
            with open(notif_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Fixed iframe frame-busting constraint in notificaciones.html")

if __name__ == "__main__":
    fix_admin_link()
    fix_iframe_redirect()
