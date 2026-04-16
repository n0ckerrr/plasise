# Directiva: Generación de Facturas PDF (SOP)

## Objetivo
Establecer un procedimiento estándar y determinista para la generación de documentos legales (facturas) en formato PDF dentro de la plataforma Plasise.

## Operaciones
1. **Recolección de Datos:** Extraer datos de la tabla `pedidos` y sus correspondientes `pedidos_detalle` (NUNCA usar `pedido_items` ya que no existe en el esquema).
2. **Formateo de Moneda:** Usar el formato `0,00 €` y asegurar que los flotantes se redondeen a 2 decimales.
3. **Cálculo de Impuestos:** Calcular el IVA (21%) dividiendo el total por 1.21 para obtener la base imponible.
4. **Envío de Respuesta:** Usar `flask.Response` para retornar los bytes del PDF directamente.

## Restricciones y Casos Borde
- **Nombres Largos:** Usar `multi_cell` en FPDF para evitar que el texto se corte.
- **CORS:** No usar `*` en orígenes con `supports_credentials=True`. Especificar dominios reales.
- **Dependencias:** Si falla el arranque con `ModuleNotFoundError`, verificar que el `Dockerfile` use `python3 -m pip install --no-cache-dir`.
- **Seguridad:** Validar siempre la propiedad del pedido en la consulta SQL: `WHERE id = %s AND usuario_id = %s`.

## Salidas Esperadas
- Archivo PDF profesional, legible y con los datos legales correctos.
- No guardar archivos basura en el servidor (generación en memoria mediante `BytesIO`).
