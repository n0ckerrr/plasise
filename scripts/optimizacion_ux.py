import os
import shutil
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend'))
INDEX_PATH = os.path.join(FRONTEND_DIR, 'pages', 'index.html')

def main():
    if not os.path.exists(INDEX_PATH):
        print("index.html not found.")
        return

    # Backup
    shutil.copy2(INDEX_PATH, INDEX_PATH + '.bak')
    print("Backup creado en index.html.bak")

    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # 1. Eliminar controles del carrusel e indicadores
    indicators = soup.find('div', class_='carousel-indicators')
    if indicators: indicators.decompose()
    
    prev_btn = soup.find('button', class_='carousel-control-prev')
    if prev_btn: prev_btn.decompose()
    
    next_btn = soup.find('button', class_='carousel-control-next')
    if next_btn: next_btn.decompose()

    # 2. Eliminar slide 2 de IA
    items = soup.find_all('div', class_='carousel-item')
    if len(items) > 1:
        items[1].decompose() # El segundo es el de Agencia IA

    # 3. Eliminar sección de "Agencia / Consultoría"
    for sec in soup.find_all('section'):
        h2 = sec.find('h2')
        if h2 and 'Tecnología Frontend & Automatización' in h2.get_text():
            sec.decompose()
            break

    # 4. Eliminar sección "Soluciones especializadas" (redundante)
    for sec in soup.find_all('section'):
        h2 = sec.find('h2')
        if h2 and 'Soluciones especializadas' in h2.get_text():
            sec.decompose()
            break

    # 5. Reescribir el contenido de Asesoría e Instalación
    for sec in soup.find_all('section'):
        h2 = sec.find('h2')
        if h2 and 'Asesoría' in h2.get_text() and 'Seguridad' in h2.get_text():
            h2.string = "Asesoría y Presupuestos Gratuitos para Profesionales"
            
            # Cambiar etiqueta de provincia
            label = sec.find('span', class_='section-label')
            if label:
                label.string = "Soporte Técnico Especializado"
            
            ps = sec.find_all('p')
            if len(ps) >= 3:
                ps[0].string = "Sabemos que diseñar un proyecto técnico desde cero lleva tiempo. A menudo surgen dudas sobre compatibilidades, distancias de cableado o licencias necesarias."
                ps[1].clear()
                ps[1].append("Te ofrecemos un ")
                strong1 = soup.new_tag("strong")
                strong1.string = "Servicio de Asesoría Gratuita y Presupuestos a Medida"
                ps[1].append(strong1)
                ps[1].append(". Escogemos el material exacto para tu instalación evitando que tu cliente adquiera productos innecesarios.")
                
                ps[2].clear()
                ps[2].append("Y para garantizar que tu proyecto sale perfecto, te prestamos nuestro servicio de ")
                strong2 = soup.new_tag("strong")
                strong2.string = "Soporte técnico remoto rápido (vía WhatsApp/Teléfono)"
                ps[2].append(strong2)
                ps[2].append(" de forma totalmente gratuita en tus primeros proyectos para ayudarte a captar clientes.")
            
            lis = sec.find_all('li')
            if len(lis) >= 3:
                # Keep the icons, just change the text
                for li in lis:
                    i_tag = li.find('i')
                    if i_tag:
                        i_tag.extract()
                        li.clear()
                        li.append(i_tag)
                
                lis[0].append(" Asesoría y diseño de presupuestos totalmente gratuitos.")
                lis[1].append(" Soporte técnico remoto rápido por WhatsApp/Teléfono.")
                lis[2].append(" Seleccionamos solo el material necesario, sin sobrecostes ni incompatibilidades.")
            break

    # 6. Cambiar Features de IA a Ventajas de Ecommerce
    features = soup.find_all('div', class_='feature')
    if len(features) >= 4:
        # Feat 1
        features[0].find('h4').string = "Soporte Inmediato"
        features[0].find('p').string = "Vía WhatsApp o teléfono directo"
        features[0].find('i')['class'] = "fas fa-headset"
        
        # Feat 2
        features[1].find('h4').string = "Ayuda en Presupuestos"
        features[1].find('p').string = "Elegimos el material ideal y compatible"
        features[1].find('i')['class'] = "fas fa-file-invoice-dollar"
        
        # Feat 3
        features[2].find('h4').string = "Stock Permanente"
        features[2].find('p').string = "Envío rápido a toda España"
        features[2].find('i')['class'] = "fas fa-box"
        
        # Feat 4
        features[3].find('h4').string = "Precios Exclusivos"
        features[3].find('p').string = "Descuentos reales para profesionales"
        features[3].find('i')['class'] = "fas fa-tags"

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print("Script completado: index.html optimizado correctamente.")

if __name__ == '__main__':
    main()
