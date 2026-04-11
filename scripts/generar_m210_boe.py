import os
import unicodedata

def format_an(text, length):
    """Format string to alphanumeric, uppercase, no accents, padded with spaces."""
    if text is None:
        text = ""
    # Remove accents
    text = unicodedata.normalize('NFD', str(text))
    text = "".join([c for c in text if unicodedata.category(c) != 'Mn'])
    # Upper case and clean special characters
    text = text.upper().replace('Ñ', 'N')
    # Keep only A-Z, 0-9 and spaces
    clean_text = ""
    for char in text:
        if char.isalnum() or char.isspace():
            clean_text += char
        else:
            clean_text += " "
    return clean_text[:length].ljust(length)

def format_num(number, length):
    """Format number to string, padded with leading zeros."""
    try:
        val = int(float(number))
    except (ValueError, TypeError):
        val = 0
    return str(abs(val)).zfill(length)[:length]

def format_importe(amount):
    """Format amount to AEAT 17-byte format: Sign + 16 digits (2 decimals)."""
    try:
        val = float(amount)
    except (ValueError, TypeError):
        val = 0.0
    
    sign = " " if val >= 0 else "N"
    cents = str(round(abs(val) * 100)).zfill(16)
    return sign + cents[:16]

def generar_registro_210(data):
    """Generates the 2700 character string for Modelo 210."""
    reg = ""
    
    # 1-8: Identificador de registro + 9: Reservado
    reg += "<T21002> " # 8 chars + 1 space = 9
    
    # 10: Tipo de declaración (I=Ingreso)
    reg += "I"
    
    # 11-19: NIF Presentador (9)
    reg += format_an(data.get('nif_presentador'), 9)
    
    # 20-144: Nombre Presentador (125)
    reg += format_an(data.get('nombre_presentador'), 125)
    
    # 145-150: Condición (X en Contribuyente) (6)
    reg += "X     "
    
    # 151: Agrupación (1)
    reg += " "
    
    # 152-153: Periodo (0A = Anual) (2)
    reg += "0A"
    
    # 154-157: Ejercicio (YYYY) (4)
    reg += format_num(data.get('ejercicio'), 4)
    
    # 158-165: Fecha Devengo (DDMMAAAA) (8)
    reg += format_num(data.get('fecha_devengo'), 8)
    
    # 166-167: Tipo Renta (02 = Uso Propio) (2)
    reg += "02"
    
    # 168-170: Divisa (3)
    reg += "EUR"
    
    # 171-179: NIF Contribuyente (9)
    reg += format_an(data.get('nif_contribuyente'), 9)
    
    # 180: F/J Contribuyente (1)
    reg += "F"
    
    # 181-305: Nombre Contribuyente (125)
    reg += format_an(data.get('nombre_contribuyente'), 125)
    
    # Pad to current 305 positions check
    # 306-320: Reservado (15)
    reg += " " * 15
    
    # ... Simplified filling for demonstration, using padEnd for the rest ...
    # 1442-1458: Base Imponible (Casilla 9)
    # We need to reach 1441 before adding Base Imponible
    reg = reg.ljust(1441)
    reg += format_importe(data.get('base_imponible', 0))
    
    # 1703-1707: Tipo gravamen (Casilla 21) (5) - format: 19.00 -> 01900
    reg = reg.ljust(1702)
    tipo_grav = float(data.get('tipo_gravamen', 0)) * 100
    reg += format_num(tipo_grav, 5)
    
    # 1708-1724: Cuota (Casilla 22) (17)
    reg += format_importe(data.get('cuota_tributaria', 0))
    
    # 1849-1865: RESULTADO (Casilla 31) (17)
    reg = reg.ljust(1848)
    reg += format_importe(data.get('cuota_tributaria', 0))
    
    # 1880-1979: Persona contacto (100)
    reg = reg.ljust(1879)
    reg += format_an(data.get('persona_contacto', 'FINCAS GENOVES SL'), 100)
    
    # Final padding to 2700
    reg = reg.ljust(2700)
    return reg

if __name__ == "__main__":
    # Ejemplo de uso
    datos_test = {
        'nif_presentador': '12345678Z',
        'nombre_presentador': 'FINCAS GENOVES SL',
        'ejercicio': 2025,
        'fecha_devengo': '31122025',
        'nif_contribuyente': 'X1234567L',
        'nombre_contribuyente': 'JOHN DOE',
        'base_imponible': 1500.50,
        'tipo_gravamen': 19.0,
        'cuota_tributaria': 285.10
    }
    
    resultado = generar_registro_210(datos_test)
    print(f"Longitud del registro: {len(resultado)}")
    
    filename = f"M210_{datos_test['nif_contribuyente']}_{datos_test['ejercicio']}.210"
    with open(filename, 'w', encoding='iso-8859-1', newline='\r\n') as f:
        f.write(resultado)
    
    print(f"Archivo generado: {filename}")
