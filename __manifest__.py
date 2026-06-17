{
    'name': 'Análisis de Consumo de Productos',
    'version': '15.0.1.0.0',
    'summary': 'Cálculo en tiempo real del consumo histórico y dinámico de productos.',
    'description': """
Análisis Avanzado de Inventario
================================
Este módulo optimiza la gestión de stock permitiendo a los analistas evaluar el consumo real de los productos.
- **Vista de Base de Datos (SQL View):** Reporte masivo (pivote/gráfico) agrupado por categorías de productos con periodos fijos (3 meses, 1 año, 3 años, histórico).
- **Asistente Dinámico en la Ficha del Producto:** Botón interactivo para calcular el consumo exacto de un producto bajo demanda, permitiendo filtros personalizados por rangos de fechas (Desde/Hasta).
- **Fórmula de Consumo:** Salidas a Clientes (Ubicaciones Cliente) menos Devoluciones de Clientes.
    """,
    'author': 'Iosmel Salazar Cuenca',
    'website': '',
    'category': 'Inventory/Inventory',
    'license': 'LGPL-3',
    
    # Dependencias clave para Odoo 15 Enterprise / Community
    'depends': [
        'base',
        'product',
        'stock',
    ],
    
    # Orden de carga crítico de los archivos XML
    'data': [
        'security/ir.model.access.csv',      # Recuerda dar permisos a report.consumo.analisis y wizard.product.consumo
        'wizard/wizard_product_consumo_view.xml',
        'wizard/wizard_rango_lista_view.xml',
        'views/product_product_view.xml',    # Aquí va la herencia de la ficha del producto
        'views/report_consumo_analisis_view.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}