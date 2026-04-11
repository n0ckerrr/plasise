"""
============================================================================
PLASISE BACKEND - VALIDATORS
Funciones de validación para datos de entrada
============================================================================
"""

import re
from email_validator import validate_email as email_val, EmailNotValidError


def validate_email(email):
    """
    Validar formato de email
    
    Args:
        email: String con el email
    
    Returns:
        bool: True si es válido
    """
    try:
        email_val(email)
        return True
    except EmailNotValidError:
        return False


def validate_password(password):
    """
    Validar fortaleza de contraseña
    
    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    
    Args:
        password: String con la contraseña
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "La contraseña es requerida"
    
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe contener al menos un número"
    
    return True, None


def validate_cif(cif):
    """
    Validar CIF español
    
    Args:
        cif: String con el CIF
    
    Returns:
        bool: True si es válido
    """
    if not cif or len(cif) != 9:
        return False
    
    # Formato: Letra + 7 dígitos + letra/dígito
    pattern = r'^[A-Z][0-9]{7}[A-Z0-9]$'
    return bool(re.match(pattern, cif.upper()))


def validate_phone(phone):
    """
    Validar teléfono (formato internacional o español)
    
    Args:
        phone: String con el teléfono
    
    Returns:
        bool: True si es válido
    """
    if not phone:
        return False
    
    # Eliminar espacios y guiones
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Formato internacional: +XXxxxxxxxxx (10-15 dígitos)
    # Formato español: 9XXXXXXXX
    pattern = r'^(\+[0-9]{10,15}|[6-9][0-9]{8})$'
    return bool(re.match(pattern, phone))


def validate_postal_code(postal_code, country='ES'):
    """
    Validar código postal
    
    Args:
        postal_code: String con el código postal
        country: País (ES, PT, FR, etc.)
    
    Returns:
        bool: True si es válido
    """
    if not postal_code:
        return False
    
    patterns = {
        'ES': r'^\d{5}$',
        'PT': r'^\d{4}-\d{3}$',
        'FR': r'^\d{5}$',
        'GB': r'^[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}$'
    }
    
    pattern = patterns.get(country, r'^\d{4,10}$')
    return bool(re.match(pattern, postal_code.upper().strip()))


def sanitize_input(text, max_length=None):
    """
    Sanitizar input de usuario
    
    Args:
        text: String a sanitizar
        max_length: Longitud máxima
    
    Returns:
        str: Texto sanitizado
    """
    if not text:
        return ''
    
    # Eliminar espacios al inicio y final
    text = text.strip()
    
    # Eliminar caracteres de control
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    # Limitar longitud
    if max_length:
        text = text[:max_length]
    
    return text


def validate_sku(sku):
    """
    Validar formato de SKU
    
    Args:
        sku: String con el SKU
    
    Returns:
        bool: True si es válido
    """
    if not sku:
        return False
    
    # Formato: Letras, números, guiones (3-50 caracteres)
    pattern = r'^[A-Z0-9\-]{3,50}$'
    return bool(re.match(pattern, sku.upper()))


def validate_price(price):
    """
    Validar precio
    
    Args:
        price: Número o string con el precio
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        price = float(price)
        
        if price < 0:
            return False, "El precio no puede ser negativo"
        
        if price > 999999.99:
            return False, "El precio es demasiado alto"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "Formato de precio inválido"


def validate_quantity(quantity):
    """
    Validar cantidad
    
    Args:
        quantity: Número o string con la cantidad
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        quantity = int(quantity)
        
        if quantity < 1:
            return False, "La cantidad debe ser al menos 1"
        
        if quantity > 10000:
            return False, "La cantidad es demasiado alta"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "Formato de cantidad inválido"
