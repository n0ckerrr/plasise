# SOP – UX/UI y Reglas de Diseño PLASISE

## Objetivo
Mantener la experiencia de usuario (UX) coherente, limpia y sin ambigüedades. El proyecto sufre de una crisis de identidad originada por la combinación de servicios de agencia IA con distribución B2B de seguridad. Este documento regula cómo deben tratarse estos contenidos.

## Diagnóstico y Reglas Core
- **Regla del 'Don't make me think':** La página de inicio (index.html) DEBE estar dedicada 100% al e-commerce B2B de seguridad. Un instalador debe saber de qué trata la página en los 3 primeros segundos.
- **Separación de Servicios:** Todo lo relacionado con 'Agencia IA', 'Chatbots', 'Automatizaciones RAG' y 'n8n' (Pla6è Solucions Agency) debe aislarse en servicios.html. NUNCA mezclarlos en el Hero o destacados de index.html.
- **Propuesta de Gran Valor (Gancho Inicial):** PLASISE ofrecerá **Asesoría Técnica Gratuita** inicial. Nuestro objetivo no es solo vender material, es *ayudarles a armar presupuestos* precisos por WhatsApp y evitarles devoluciones por incompatibilidades. Esto debe ser el foco de la sección de beneficios.

## Restricciones y Casos Borde
- Al limpiar HTMLs, no usar herramientas de edición directa si se puede evitar; usar un script de Python idempotente para garantizar que si el script falla, el HTML se puede reconstruir (hacer backup antes de modificar).
- **Asesoría Gratuita:** Mencionar explícitamente que la ayuda técnica para crear presupuestos es gratuita para los primeros contactos/proyectos. Evitar textos ambiguos. El botón CTA de ayuda debe dirigir a WhatsApp (https://wa.me/34684782268).
