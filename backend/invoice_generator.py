from fpdf import FPDF
from datetime import datetime
import io

class PlasiseInvoice(FPDF):
    def header(self):
        # Fondo decorativo superior (Barra negra elegante)
        self.set_fill_color(10, 10, 15) # --primary color
        self.rect(0, 0, 210, 40, 'F')
        
        # Logo o Nombre Empresa en blanco sobre fondo negro
        self.set_font('helvetica', 'B', 32)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 12)
        self.cell(0, 10, 'PLASISE', ln=False, align='L')
        
        # Subtítulo en Gold (Accent)
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(200, 164, 94) # --accent color
        self.set_xy(10, 25)
        self.cell(0, 5, 'EXCELENCIA EN SEGURIDAD ELECTRONICA', ln=True, align='L')
        
        # Datos del Emisor en blanco (Derecha)
        self.set_font('helvetica', '', 9)
        self.set_text_color(220, 220, 220)
        self.set_xy(120, 10)
        self.cell(80, 5, 'PLASISE S.A. | NIF: B-55238122', ln=True, align='R')
        self.set_x(120)
        self.cell(80, 5, 'Calle del Progreso, 123 (P.I. Montfullà)', ln=True, align='R')
        self.set_x(120)
        self.cell(80, 5, '17190 Salt, Girona (Espanya)', ln=True, align='R')
        self.set_x(120)
        self.cell(80, 5, 'T: +34 972 00 00 00 | E: admin@plasise.es', ln=True, align='R')

        self.set_y(50)

    def footer(self):
        self.set_y(-35)
        # Línea decorativa
        self.set_draw_color(200, 164, 94)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 4, 'Este documento es una Factura Proforma generada para el control administrativo del cliente. El pago se regirá por las condiciones pactadas. Para soporte técnico o consultas post-venta, contacte vía WhatsApp al +34 600 000 000.', align='C')
        
        self.ln(2)
        self.set_font('helvetica', '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Plasise Business Platform', align='C')


def generate_invoice_pdf(order_data):
    """
    Genera un PDF profesional en memoria.
    order_data: {id, fecha, total, items, cliente_nombre, cliente_email, direccion, cif}
    """
    pdf = PlasiseInvoice()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=40)
    
    # Título de Documento
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(10, 10, 15)
    pdf.set_y(50)
    pdf.cell(0, 10, f'FACTURA PROFORMA: #INV-{order_data.get("id", "0000")}', ln=True)
    pdf.ln(2)
    
    # Bloque de Información Cliente y Pedido (Diseño en columnas)
    y_start = pdf.get_y()
    
    # Columna Izquierda: Cliente
    pdf.set_fill_color(250, 250, 250)
    pdf.rect(10, y_start, 90, 35, 'F')
    pdf.set_xy(15, y_start + 5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(10, 10, 15)
    pdf.cell(80, 5, 'DATOS DE FACTURACIÓN', ln=True)
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(15)
    pdf.cell(80, 5, f'Cliente: {order_data.get("cliente_nombre", "Consumidor Final")}', ln=True)
    pdf.set_x(15)
    pdf.cell(80, 5, f'CIF/NIF: {order_data.get("cif", "En archivo")}', ln=True)
    pdf.set_x(15)
    pdf.multi_cell(80, 4, f'Dirección: {order_data.get("direccion", "Consultar perfil")}')
    
    # Columna Derecha: Pedido
    pdf.set_xy(110, y_start)
    pdf.set_fill_color(250, 250, 250)
    pdf.rect(110, y_start, 90, 35, 'F')
    pdf.set_xy(115, y_start + 5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(10, 10, 15)
    pdf.cell(80, 5, 'DETALLES DE ORDEN', ln=True)
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(115)
    pdf.cell(80, 5, f'Fecha Emisión: {order_data.get("fecha", datetime.now().strftime("%d/%m/%Y"))}', ln=True)
    pdf.set_x(115)
    pdf.cell(80, 5, f'Método Pago: {str(order_data.get("metodo_pago", "Transferencia")).upper()}', ln=True)
    pdf.set_x(115)
    pdf.cell(80, 5, f'Estado: {str(order_data.get("estado", "Confirmado")).upper()}', ln=True)
    
    pdf.set_y(y_start + 45)
    
    # Tabla de Productos
    pdf.set_fill_color(10, 10, 15)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(10, 10, 'Pos', border=0, fill=True, align='C')
    pdf.cell(100, 10, ' Descripción del Producto', border=0, fill=True)
    pdf.cell(25, 10, 'Cant.', border=0, fill=True, align='C')
    pdf.cell(25, 10, 'Precio U.', border=0, fill=True, align='R')
    pdf.cell(30, 10, 'Subtotal ', border=0, fill=True, align='R')
    pdf.ln()
    
    # Líneas
    pdf.set_text_color(60, 60, 60)
    pdf.set_font('helvetica', '', 9)
    items = order_data.get('items', [])
    
    for i, item in enumerate(items, 1):
        nombre = str(item.get('nombre', 'Producto Sin Nombre'))
        qty = int(item.get('cantidad', 1))
        price = float(item.get('precio_unitario', 0))
        sub = qty * price
        
        # Zebra striping
        fill = (i % 2 == 0)
        pdf.set_fill_color(248, 248, 248)
        
        # Calcular altura celda multilínea
        start_y = pdf.get_y()
        pdf.set_xy(20, start_y)
        pdf.multi_cell(100, 8, f' {nombre}', border=0, fill=fill)
        end_y = pdf.get_y()
        h = end_y - start_y
        
        # Dibujar el resto de celdas de la fila con la altura calculada
        pdf.set_xy(10, start_y)
        pdf.cell(10, h, str(i), border=0, fill=fill, align='C')
        pdf.set_xy(120, start_y)
        pdf.cell(25, h, str(qty), border=0, fill=fill, align='C')
        pdf.cell(25, h, f'{price:,.2f} ', border=0, fill=fill, align='R')
        pdf.cell(30, h, f'{sub:,.2f} ', border=0, fill=fill, align='R')
        pdf.set_y(end_y)

    # Totales
    pdf.ln(10)
    total_eur = float(order_data.get('total', 0))
    subtotal_base = total_eur / 1.21
    iva_amount = total_eur - subtotal_base
    
    pdf.set_x(120)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(40, 7, 'BASE IMPONIBLE:', ln=0, align='R')
    pdf.set_font('helvetica', '', 10)
    pdf.cell(30, 7, f'{subtotal_base:,.2f} EUR ', ln=1, align='R')
    
    pdf.set_x(120)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(40, 7, 'IVA (21%):', ln=0, align='R')
    pdf.set_font('helvetica', '', 10)
    pdf.cell(30, 7, f'{iva_amount:,.2f} EUR ', ln=1, align='R')
    
    pdf.ln(2)
    pdf.set_x(120)
    pdf.set_fill_color(10, 10, 15)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(40, 12, 'TOTAL FACTURA:', border=0, fill=True, align='R')
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(30, 12, f'{total_eur:,.2f} EUR ', border=0, fill=True, align='R')
    
    return pdf.output()
