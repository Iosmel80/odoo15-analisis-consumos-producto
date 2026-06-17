from odoo import models, fields, api

class WizardRangoLista(models.TransientModel):
    _name = 'wizard.rango.lista'
    _description = 'Filtro de Consumo por Rango para Listado'

    fecha_desde = fields.Date(string="Fecha Desde", required=True)
    fecha_hasta = fields.Date(string="Fecha Hasta", required=True)

    def action_aplicar_filtro_lista(self):
        """ Recarga la vista de lista inyectando el rango personalizado en el contexto """
        self.ensure_one()
        
        # Buscamos la acción nativa que abre el catálogo de productos
        action = self.env["ir.actions.actions"]._for_xml_id("product.product_template_action_product")
        
        # Forzamos nuestro contexto personalizado sin perder el filtro por defecto
        new_context = dict(self._context or {})
        new_context.update({
            'filtro_consumo': 'rango',
            'consumo_fecha_desde': self.fecha_desde,
            'consumo_fecha_hasta': self.fecha_hasta,
            'search_default_filter_to_sell': 1 # Mantiene activos los productos para vender
        })
        
        action['context'] = new_context
        return action