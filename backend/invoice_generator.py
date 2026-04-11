from fpdf import FPDF
from datetime import datetime
import io

class PlasiseInvoice(FPDF):
    def header(self):
        # Logo o Nombre Empresa
        self.set_font('helvetica', 'B', 24)
        self.set_text_color(10, 10, 15) # --primary color
        self.cell(0, 10, 'PLASISE', ln=True, align='L')
        
        # Subtítulo
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(200, 164, 94) # --accent color
        self.cell(0, 5, 'EXCELENCIA EN SEGURIDAD ELECTRONICA', ln=True, align='L')
        
        # Datos Emisor (Genéricos por ahora)
        self.set_font('helvetica', '', 9)
        self.set_text_color(100, 100, 100)
        self.set_y(10)
        self.cell(0, 5, 'PLASISE S.A.', ln=True, align='R')
        self.cell(0, 5, 'NIF: B-00000000', ln=True, align='R')
        self.cell(0, 5, 'Calle del Progreso, 123', ln=True, align='R')
        self.cell(0, 5, '17001 Girona, Espana', ln=True, align='R')

        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, 'Gracias por su confianza en PLASISE.', align='C', ln=True)
        self.set_font('helvetica', '', 7)
        self.multi_cell(0, 4, 'Documento generado automaticamente. Esta factura es valida para fines profesionales de seguimiento y control. Para cualquier reclamacion tecnica, contacte con soporte tecnico via WhatsApp.', align='C')

        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', align='R')


def generate_invoice_pdf(order_data):
    """
    Genera un PDF en memoria para un pedido dado.
    order_data debe contener: id, fecha_pedido, total, items, cliente_nombre, cliente_email, etc.
    """
    pdf = PlasiseInvoice()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=30)
    
    # Bloque de Información del Pedido y Cliente
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f'FACTURA PROFORMA: #{order_data["id"]}', ln=True)
    pdf.ln(5)
    
    # Cuadrícula Cliente / Pedido
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(95, 7, 'DATOS DEL CLIENTE', ln=0)
    pdf.cell(95, 7, 'DETALLES DEL PEDIDO', ln=1)
    
    pdf.set_font('helvetica', '', 10)
    # Fila 1
    pdf.cell(95, 6, f'Nombre: {order_data.get("cliente_nombre", "N/A")}', ln=0)
    pdf.cell(95, 6, f'Fecha: {order_data.get("fecha_pedido", "N/A")}', ln=1)
    # Fila 2
    pdf.cell(95, 6, f'Email: {order_data.get("cliente_email", "N/A")}', ln=0)
    pdf.cell(95, 6, f'Estado: {order_data.get("estado", "Pendiente").upper()}', ln=1)
    
    pdf.ln(15)
    
    # Tabla de Productos (Cabecera)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(100, 10, ' PRODUCTO', border=1, fill=True)
    pdf.cell(30, 10, ' CANT.', border=1, fill=True, align='C')
    pdf.cell(30, 10, ' PRECIO U.', border=1, fill=True, align='R')
    pdf.cell(30, 10, ' TOTAL', border=1, fill=True, align='R')
    pdf.ln()
    
    # Líneas de Productos
    pdf.set_font('helvetica', '', 9)
    items = order_data.get('items', [])
    for item in items:
        # Pre-calculamos altura si el nombre es largo
        nombre = str(item.get('nombre', 'Producto'))
        pdf.cell(100, 8, f' {nombre[:50]}...', border=1)
        pdf.cell(30, 8, str(item.get('cantidad', 1)), border=1, align='C')
        pdf.cell(30, 8, f'{float(item.get("precio_unitario", 0)):.2f} ', border=1, align='R')
        total_item = float(item.get("precio_unitario", 0)) * int(item.get("cantidad", 1))
        pdf.cell(30, 8, f'{total_item:.2f} ', border=1, align='R')
        pdf.ln()

    pdf.ln(5)
    
    # Totales
    total_raw = float(order_data.get('total', 0))
    subtotal = total_raw / 1.21
    iva = total_raw - subtotal
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(130, 7, '', ln=0)
    pdf.cell(30, 7, 'Subtotal:', ln=0, align='R')
    pdf.cell(30, 7, f'{subtotal:.2f} ', ln=1, align='R')
    
    pdf.cell(130, 7, '', ln=0)
    pdf.cell(30, 7, 'IVA (21%):', ln=0, align='R')
    pdf.cell(30, 7, f'{iva:.2f} ', ln=1, align='R')
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(200, 164, 94) # --accent
    pdf.cell(130, 10, '', ln=0)
    pdf.cell(30, 10, 'TOTAL EUR:', ln=0, align='R')
    pdf.cell(30, 10, f'{total_raw:.2f} EUR ', ln=1, align='R')

    
    # Retornar como BytesIO
    return pdf.output()
