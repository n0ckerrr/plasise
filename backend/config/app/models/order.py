"""
============================================================================
PLASISE BACKEND - ORDER MODEL
Modelo de pedido con gestión completa del flujo de compra
============================================================================
"""

from app.utils.database import db
from datetime import datetime
import secrets

class Order:
    """Modelo de Pedido"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.numero_pedido = data.get('numero_pedido')
            self.usuario_id = data.get('usuario_id')
            self.empresa_id = data.get('empresa_id')
            self.fecha = data.get('fecha')
            self.estado = data.get('estado', 'pendiente')
            self.subtotal = data.get('subtotal', 0)
            self.descuento = data.get('descuento', 0)
            self.gastos_envio = data.get('gastos_envio', 0)
            self.impuestos = data.get('impuestos', 0)
            self.total = data.get('total', 0)
            self.metodo_pago = data.get('metodo_pago')
            self.estado_pago = data.get('estado_pago', 'pendiente')
    
    @staticmethod
    def create_from_cart(usuario_id, direccion_envio, metodo_pago, notas=None):
        """Crear pedido desde el carrito del usuario"""
        
        # Obtener items del carrito
        cart_items = db.execute_query("""
            SELECT * FROM pedidos_detalle pd
            INNER JOIN pedidos p ON pd.pedido_id = p.id
            WHERE p.usuario_id = %s AND p.estado = 'carrito'
        """, (usuario_id,))
        
        if not cart_items:
            raise ValueError("Carrito vacío")
        
        # Generar número de pedido
        numero_pedido = Order.generate_order_number()
        
        # Calcular totales
        subtotal = sum(item['subtotal'] for item in cart_items)
        impuestos = subtotal * 0.21  # IVA 21%
        total = subtotal + impuestos
        
        # Crear pedido
        pedido_data = {
            'numero_pedido': numero_pedido,
            'usuario_id': usuario_id,
            'estado': 'pendiente',
            'subtotal': subtotal,
            'impuestos': impuestos,
            'total': total,
            'metodo_pago': metodo_pago,
            'direccion_envio': direccion_envio,
            'notas_cliente': notas
        }
        
        pedido_id = db.insert('pedidos', pedido_data)
        
        # Mover items del carrito al pedido
        # ... (implementar lógica)
        
        return pedido_id
    
    @staticmethod
    def generate_order_number():
        """Generar número de pedido único"""
        date_part = datetime.now().strftime('%Y%m%d')
        
        # Obtener último número del día
        query = """
        SELECT numero_pedido FROM pedidos
        WHERE numero_pedido LIKE %s
        ORDER BY id DESC LIMIT 1
        """
        result = db.get_one(query, (f'PED-{date_part}%',))
        
        if result:
            last_num = int(result['numero_pedido'].split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"PED-{date_part}-{next_num:06d}"
    
    @staticmethod
    def find_by_id(order_id):
        """Buscar pedido por ID con detalles"""
        query = """
        SELECT p.*, u.nombre, u.email
        FROM pedidos p
        INNER JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id = %s
        """
        result = db.get_one(query, (order_id,))
        
        if not result:
            return None
        
        order = Order(result)
        
        # Cargar items
        order.items = db.execute_query(
            "SELECT * FROM pedidos_detalle WHERE pedido_id = %s",
            (order_id,)
        )
        
        return order
    
    def update_status(self, nuevo_estado):
        """Actualizar estado del pedido"""
        return db.update(
            'pedidos',
            {'estado': nuevo_estado},
            'id = %s',
            [self.id]
        )
