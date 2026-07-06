# Análisis de Consumo de Productos para Odoo 15

Este módulo está diseñado para ayudar a las empresas a entender el comportamiento real de consumo de sus productos a partir del historial de movimientos de inventario en Odoo. Proporciona una visión más clara, rápida y accionable del stock, facilitando la toma de decisiones en compras, planificación y control de inventario.

## ¿Qué hace este módulo?

El módulo transforma la información de movimientos de stock en indicadores de consumo útiles para el negocio. Permite analizar cuánto se ha consumido un producto en distintos periodos de tiempo y visualizar esa información directamente desde la ficha del producto, la vista de listado y un reporte consolidado de inventario.

## Funcionalidades principales

- Análisis de consumo por producto en periodos fijos:
  - Últimos 3 meses
  - Último año
  - Últimos 3 años
  - Consumo histórico total

- Cálculo de consumo personalizado mediante un asistente:
  - Permite definir un rango de fechas específico
  - Muestra el consumo del producto dentro de ese periodo
  - Incluye fechas de primer y último consumo registrado

- Vista consolidada de inventario y consumo:
  - Información de existencia
  - Existencia total
  - Existencias por almacén o ubicación
  - Pedidos de compra pendientes
  - Proveedores asociados
  - Precio promedio y cantidades mínimas/máximas de reabastecimiento

- Integración directa con la ficha del producto:
  - Se agregan campos visuales de consumo en la vista de formulario
  - Se incorpora un botón para abrir el análisis avanzado por rango

- Filtros dinámicos en el listado de productos:
  - Filtrado rápido por consumo en los últimos 3 meses
  - Filtrado por último año
  - Filtrado por últimos 3 años
  - Filtro personalizado por fechas

## Valor de negocio

Este módulo permite a los equipos de compras, almacén e inventario responder preguntas clave como:

- ¿Qué productos tienen mayor consumo real?
- ¿Cuánto se ha movido un producto en los últimos meses?
- ¿Cuál es el comportamiento histórico de un artículo?
- ¿Qué productos requieren mayor atención o reabastecimiento?

Con esta información, la empresa puede mejorar la planificación de compras, evitar desabastecimientos y tener mejor control sobre el inventario.

## Requisitos

- Odoo 15 Community o Enterprise
- Módulos base de Odoo:
  - base
  - product
  - stock

## Instalación

1. Copia este módulo dentro de la carpeta de addons de tu instancia de Odoo.
2. Actualiza la lista de módulos desde la interfaz de Odoo.
3. Busca el módulo llamado "Análisis de Consumo de Productos".
4. Instálalo y habilítalo para los usuarios con acceso a inventario.

## Uso recomendado

Una vez instalado, el usuario podrá:

- Entrar a la ficha de un producto y ver sus indicadores de consumo.
- Abrir el asistente de análisis para ver el consumo en un periodo definido.
- Consultar la vista de análisis de inventario desde el menú de reportes de stock.
- Utilizar filtros en el listado de productos para analizar consumos por rango temporal.

## Estructura del módulo

- Modelos: lógica de cálculo de consumo y vistas SQL de análisis
- Vistas: formularios, árboles, pivotes y menús
- Asistentes: análisis personalizado por producto y filtros de rango para listado
- Seguridad: permisos para usuarios de stock

## Notas técnicas

El cálculo de consumo se basa en los movimientos de stock con estado completado y considera los movimientos que representan salidas a clientes y devoluciones, generando un indicador de consumo más cercano al uso real del producto.

## Licencia

Este módulo se distribuye bajo licencia LGPL-3.

## Autor

Iosmel Salazar Cuenca
