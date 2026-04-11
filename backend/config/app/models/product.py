"""
============================================================================
PLASISE BACKEND - PRODUCT MODEL
Modelo completo de producto con todas sus relaciones
============================================================================
"""

from app.utils.database import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Product:
    """Modelo de Producto"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.sku = data.get('sku')
            self.ean = data.get('ean')
            self.nombre = data.get('nombre')
            self.slug = data.get('slug')
            self.descripcion_corta = data.get('descripcion_corta')
            self.descripcion_larga = data.get('descripcion_larga')
            self.categoria_id = data.get('categoria_id')
            self.marca_id = data.get('marca_id')
            self.precio_base = data.get('precio_base')
            self.precio_pvp_recomendado = data.get('precio_pvp_recomendado')
            self.stock_actual = data.get('stock_actual', 0)
            self.imagen_principal = data.get('imagen_principal')
            self.estado = data.get('estado', 'activo')
            self.destacado = data.get('destacado', 0)
            self.activo = data.get('activo', 1)
    
    @staticmethod
    def find_by_id(product_id, include_details=True):
        """Buscar producto por ID con detalles"""
        query = "SELECT * FROM v_productos_completos WHERE id = %s"
        result = db.get_one(query, (product_id,))
        
        if not result:
            return None
        
        product = Product(result)
        
        if include_details:
            # Cargar imágenes
            product.imagenes = db.execute_query(
                "SELECT * FROM productos_imagenes WHERE producto_id = %s ORDER BY orden",
                (product_id,)
            )
            
            # Cargar atributos
            product.atributos = db.execute_query(
                "SELECT * FROM productos_atributos WHERE producto_id = %s ORDER BY orden",
                (product_id,)
            )
            
            # Cargar relacionados
            product.relacionados = db.execute_query(
                """SELECT p.* FROM productos p
                   INNER JOIN productos_relacionados pr ON p.id = pr.producto_relacionado_id
                   WHERE pr.producto_id = %s AND p.activo = 1
                   LIMIT 6""",
                (product_id,)
            )
        
        return product
    
    @staticmethod
    def find_by_sku(sku):
        """Buscar producto por SKU"""
        query = "SELECT * FROM v_productos_completos WHERE sku = %s"
        result = db.get_one(query, (sku,))
        return Product(result) if result else None
    
    @staticmethod
    def search(filters=None, page=1, per_page=20):
        """
        Buscar productos con filtros avanzados
        
        Args:
            filters: Dict con filtros {
                'categoria_id': int,
                'marca_id': int,
                'search': str,
                'min_price': float,
                'max_price': float,
                'estado': str,
                'destacado': bool,
                'sort': str (price_asc, price_desc, name, newest, popular)
            }
            page: Número de página
            per_page: Items por página
        
        Returns:
            dict con {products, total, pages, current_page}
        """
        filters = filters or {}
        
        query = "SELECT * FROM v_productos_completos WHERE 1=1"
        params = []
        
        # Filtro por categoría
        if filters.get('categoria_id'):
            query += " AND categoria_id = %s"
            params.append(filters['categoria_id'])
        
        # Filtro por marca
        if filters.get('marca_id'):
            query += " AND marca_id = %s"
            params.append(filters['marca_id'])
        
        # Búsqueda por texto
        if filters.get('search'):
            query += """ AND (
                nombre LIKE %s OR 
                sku LIKE %s OR 
                descripcion_corta LIKE %s
            )"""
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])
        
        # Filtro por precio
        if filters.get('min_price'):
            query += " AND precio_base >= %s"
            params.append(float(filters['min_price']))
        
        if filters.get('max_price'):
            query += " AND precio_base <= %s"
            params.append(float(filters['max_price']))
        
        # Filtro por estado
        if filters.get('estado'):
            query += " AND estado = %s"
            params.append(filters['estado'])
        
        # Filtro por destacado
        if filters.get('destacado'):
            query += " AND destacado = 1"
        
        # Solo productos activos
        query += " AND activo = 1"
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        total = db.get_one(count_query, params)['total']
        
        # Ordenamiento
        sort_mapping = {
            'price_asc': 'precio_base ASC',
            'price_desc': 'precio_base DESC',
            'name': 'nombre ASC',
            'newest': 'fecha_creacion DESC',
            'popular': 'ventas_totales DESC'
        }
        sort_order = sort_mapping.get(filters.get('sort'), 'nombre ASC')
        query += f" ORDER BY {sort_order}"
        
        # Paginación
        query += f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"
        
        # Ejecutar
        products = db.execute_query(query, params)
        
        return {
            'products': products,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page,
            'per_page': per_page
        }
    
    @staticmethod
    def create(data):
        """Crear nuevo producto"""
        from slugify import slugify
        
        # Generar slug si no existe
        if 'slug' not in data:
            data['slug'] = slugify(data['nombre'])
        
        # Valores por defecto
        data.setdefault('estado', 'activo')
        data.setdefault('activo', 1)
        data.setdefault('destacado', 0)
        data.setdefault('stock_actual', 0)
        
        return db.insert('productos', data)
    
    def update(self, data):
        """Actualizar producto"""
        protected_fields = ['id', 'fecha_creacion']
        data = {k: v for k, v in data.items() if k not in protected_fields}
        
        if not data:
            return 0
        
        return db.update('productos', data, 'id = %s', [self.id])
    
    def delete(self, hard=False):
        """Eliminar producto (soft delete por defecto)"""
        if hard:
            return db.delete('productos', 'id = %s', [self.id])
        else:
            return db.update('productos', {'activo': 0}, 'id = %s', [self.id])
    
    def update_stock(self, cantidad, operacion='add'):
        """
        Actualizar stock del producto
        
        Args:
            cantidad: Cantidad a sumar o restar
            operacion: 'add' o 'subtract'
        """
        if operacion == 'add':
            query = "UPDATE productos SET stock_actual = stock_actual + %s WHERE id = %s"
        else:
            query = "UPDATE productos SET stock_actual = stock_actual - %s WHERE id = %s"
        
        return db.execute_query(query, (cantidad, self.id), fetch=False, commit=True)
    
    def increment_views(self):
        """Incrementar contador de vistas"""
        return db.execute_query(
            "UPDATE productos SET vistas = vistas + 1 WHERE id = %s",
            (self.id,),
            fetch=False,
            commit=True
        )
    
    def increment_sales(self, cantidad=1):
        """Incrementar contador de ventas"""
        return db.execute_query(
            "UPDATE productos SET ventas_totales = ventas_totales + %s WHERE id = %s",
            (cantidad, self.id),
            fetch=False,
            commit=True
        )
    
    def add_image(self, url, tipo='galeria', orden=0):
        """Añadir imagen al producto"""
        return db.insert('productos_imagenes', {
            'producto_id': self.id,
            'url': url,
            'tipo': tipo,
            'orden': orden
        })
    
    def add_attribute(self, nombre, valor, tipo='tecnico', unidad=None, orden=0):
        """Añadir atributo técnico"""
        return db.insert('productos_atributos', {
            'producto_id': self.id,
            'nombre': nombre,
            'valor': valor,
            'tipo': tipo,
            'unidad': unidad,
            'orden': orden
        })
    
    def get_price_for_customer(self, tipo_cliente='retail'):
        """Obtener precio según tipo de cliente"""
        query = """
        SELECT precio FROM precios_clientes
        WHERE producto_id = %s AND tipo_cliente = %s AND activo = 1
        """
        result = db.get_one(query, (self.id, tipo_cliente))
        
        if result:
            return float(result['precio'])
        
        return float(self.precio_base)
    
    def check_stock(self, cantidad):
        """Verificar si hay stock disponible"""
        return self.stock_actual >= cantidad
    
    def to_dict(self, include_details=False):
        """Convertir a diccionario"""
        data = {
            'id': self.id,
            'sku': self.sku,
            'nombre': self.nombre,
            'slug': self.slug,
            'descripcion_corta': self.descripcion_corta,
            'precio_base': float(self.precio_base),
            'stock_actual': self.stock_actual,
            'imagen_principal': self.imagen_principal,
            'estado': self.estado,
            'destacado': bool(self.destacado),
            'activo': bool(self.activo)
        }
        
        if include_details:
            data.update({
                'descripcion_larga': self.descripcion_larga,
                'ean': self.ean,
                'categoria_id': self.categoria_id,
                'marca_id': self.marca_id,
                'precio_pvp_recomendado': float(self.precio_pvp_recomendado) if self.precio_pvp_recomendado else None,
                'imagenes': getattr(self, 'imagenes', []),
                'atributos': getattr(self, 'atributos', []),
                'relacionados': getattr(self, 'relacionados', [])
            })
        
        return data
    
    @staticmethod
    def get_featured(limit=8):
        """Obtener productos destacados"""
        query = """
        SELECT * FROM v_productos_completos
        WHERE destacado = 1 AND activo = 1
        ORDER BY orden DESC, ventas_totales DESC
        LIMIT %s
        """
        return db.execute_query(query, (limit,))
    
    @staticmethod
    def get_best_sellers(limit=10):
        """Obtener productos más vendidos"""
        query = """
        SELECT * FROM v_productos_completos
        WHERE activo = 1
        ORDER BY ventas_totales DESC
        LIMIT %s
        """
        return db.execute_query(query, (limit,))
    
    @staticmethod
    def get_new_arrivals(limit=10):
        """Obtener últimos productos añadidos"""
        query = """
        SELECT * FROM v_productos_completos
        WHERE activo = 1 AND nuevo = 1
        ORDER BY fecha_creacion DESC
        LIMIT %s
        """
        return db.execute_query(query, (limit,))
