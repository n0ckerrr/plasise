# Directiva: Generación de Facturas PDF (SOP)

## Objetivo
Establecer un procedimiento estándar y determinista para la generación de documentos legales (facturas) en formato PDF dentro de la plataforma Plasise.

## Operaciones
1. **Recolección de Datos:** Extraer datos de la tabla `pedidos` y sus correspondientes `pedido_items`.
2. **Formateo de Moneda:** Usar `Intl.NumberFormat` (JS) o `locale` (Python) para asegurar que los precios en el PDF sigan el formato `0,00 €`.
3. **Cálculo de Impuestos:** Calcular el IVA (21% por defecto) de forma desglosada a partir del subtotal.
4. **Envío de Respuesta:** La API debe servir el archivo como un stream binario con los headers `Content-Type: application/pdf` y `Content-Disposition: attachment`.

## Restricciones y Casos Borde
- **Nombres Largos:** Si el nombre de un producto es muy largo, debe truncarse o saltar de línea para no desbordar la tabla.
- **Letras Especiales:** Asegurar el uso de fuentes que soporten caracteres españoles (ñ, acentos) y el símbolo del Euro (€).
- **Seguridad:** Solo el usuario dueño del pedido (o un administrador) puede generar el PDF de dicho pedido (validar `session['user_id']`).

## Salidas Esperadas
- Archivo PDF profesional, legible y con los datos legales correctos.
- No guardar archivos basura en el servidor (generación en memoria mediante `BytesIO`).
