"""
PLASISE - Integración con Holded
"""

import requests
import json

HOLDED_API_KEY = '5cc163c45bd3b739628642bdf89506c7'
HOLDED_BASE_URL = 'https://api.holded.com/api/invoicing/v1'

def holded_request(method, endpoint, data=None):
    url = f"{HOLDED_BASE_URL}/{endpoint}"
    headers = {
        'key': HOLDED_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        else:
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Error Holded: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error en petición Holded: {e}")
        return None


def crear_factura_holded(pedido, datos_usuario, items):
    try:
        lineas = []
        for item in items:
            linea = {
                'name': item.get('nombre', 'Producto'),
                'desc': f"SKU: {item.get('sku', 'N/A')}",
                'units': item.get('cantidad', 1),
                'subtotal': float(item.get('precio', 0)),
                'tax': 21
            }
            lineas.append(linea)
        
        factura_data = {
            'contactName': f"{datos_usuario.get('nombre', '')} {datos_usuario.get('apellidos', '')}".strip(),
            'contactEmail': datos_usuario.get('email', ''),
            'desc': f"Pedido PLASISE #{pedido.get('id', '')}",
            'items': lineas,
            'notes': pedido.get('notas', ''),
            'language': 'es',
            'currency': 'EUR'
        }
        
        resultado = holded_request('POST', 'documents/invoice', factura_data)
        
        if resultado:
            return {
                'success': True,
                'factura_id': resultado.get('id'),
                'error': None
            }
        else:
            return {
                'success': False,
                'factura_id': None,
                'error': 'Error al crear factura'
            }
            
    except Exception as e:
        return {
            'success': False,
            'factura_id': None,
            'error': str(e)
        }
