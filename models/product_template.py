from odoo import models, fields, api
from datetime import date, datetime, time

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Declaración de campos del formulario
    consumo_3m = fields.Float(string="Últimos 3 Meses", compute="_compute_consumos", store=False)
    consumo_1y = fields.Float(string="Último Año", compute="_compute_consumos", store=False)
    consumo_3y = fields.Float(string="Últimos 3 Años", compute="_compute_consumos", store=False)
    consumo_historico = fields.Float(string="Consumo Histórico Total", compute="_compute_consumos", store=False)

    # Campo dinámico exclusivo para la vista de Lista (Tree)
    consumo_filtrado = fields.Float(string="Consumo", compute="_compute_consumo_filtrado", store=False)

    @api.depends('product_variant_ids')
    def _compute_consumos(self):
        """ Mantiene los datos fijos dentro de la ficha del producto de forma masiva """
        hoy = date.today()
        # Mapeo masivo inicial para evitar llamadas individuales al ORM
        # product_variant_ids.ids en lote extrae la relación sin penalización
        template_by_variant = {v.id: t for t in self for v in t.product_variant_ids}
        variant_ids = tuple(template_by_variant.keys())

        # Inicializar todos los registros en cero de un solo golpe
        for template in self:
            template.update({'consumo_3m': 0.0, 'consumo_1y': 0.0, 'consumo_3y': 0.0, 'consumo_historico': 0.0})

        if not variant_ids:
            return

        query = """
            SELECT 
                sm.product_id,
                SUM(CASE WHEN sm.date >= %s THEN (CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END) ELSE 0 END) as c_3m,
                SUM(CASE WHEN sm.date >= %s THEN (CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END) ELSE 0 END) as c_1y,
                SUM(CASE WHEN sm.date >= %s THEN (CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END) ELSE 0 END) as c_3y,
                SUM(CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END) as c_hist
            FROM stock_move sm
            JOIN stock_location src_loc ON sm.location_id = src_loc.id
            JOIN stock_location dest_loc ON sm.location_dest_id = dest_loc.id
            WHERE sm.state = 'done' AND sm.product_id IN %s
            GROUP BY sm.product_id
        """
        # Explotamos los límites relativos con strings limpios de fecha nativa
        from dateutil.relativedelta import relativedelta
        self._cr.execute(query, (hoy - relativedelta(months=3), hoy - relativedelta(years=1), hoy - relativedelta(years=3), variant_ids))
        
        # Procesamos la respuesta agrupada mapeando variantes a sus respectivos templates
        for row in self._cr.dictfetchall():
            template = template_by_variant.get(row['product_id'])
            if template:
                template.consumo_3m += row['c_3m'] or 0.0
                template.consumo_1y += row['c_1y'] or 0.0
                template.consumo_3y += row['c_3y'] or 0.0
                template.consumo_historico += row['c_hist'] or 0.0

    def _compute_consumo_filtrado(self):
        """ Evalúa el contexto activo de manera masiva y eficiente para el listado Tree """
        hoy = date.today()
        context = self._context or {}
        
        fecha_desde = None
        fecha_hasta = None

        # Evaluación unificada de rangos temporales
        if context.get('filtro_consumo') == '3m':
            from dateutil.relativedelta import relativedelta
            fecha_desde = hoy - relativedelta(months=3)
        elif context.get('filtro_consumo') == '1y':
            from dateutil.relativedelta import relativedelta
            fecha_desde = hoy - relativedelta(years=1)
        elif context.get('filtro_consumo') == '3y':
            from dateutil.relativedelta import relativedelta
            fecha_desde = hoy - relativedelta(years=3)
        elif context.get('filtro_consumo') == 'rango':
            fecha_desde = context.get('consumo_fecha_desde')
            fecha_hasta = context.get('consumo_fecha_hasta')

        # Control de sanidad para fechas en formato String/Date a Datetime (Requerido por sm.date)
        if fecha_desde and isinstance(fecha_desde, (date, str)):
            fecha_desde = datetime.combine(fields.Date.from_string(fecha_desde), time.min)
        if fecha_hasta and isinstance(fecha_hasta, (date, str)):
            fecha_hasta = datetime.combine(fields.Date.from_string(fecha_hasta), time.max)

        # Mapeo estructural de variantes a plantillas
        template_by_variant = {v.id: t for t in self for v in t.product_variant_ids}
        variant_ids = tuple(template_by_variant.keys())

        for template in self:
            template.consumo_filtrado = 0.0

        if not variant_ids:
            return

        # Query única masiva filtrada y agrupada
        query = """
            SELECT sm.product_id,
                   SUM(CASE 
                        WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty
                        WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty
                        ELSE 0 
                       END) as total
            FROM stock_move sm
            JOIN stock_location src_loc ON sm.location_id = src_loc.id
            JOIN stock_location dest_loc ON sm.location_dest_id = dest_loc.id
            WHERE sm.state = 'done' AND sm.product_id IN %s
        """
        params = [variant_ids]

        if fecha_desde:
            query += " AND sm.date >= %s"
            params.append(fecha_desde)
        if fecha_hasta:
            query += " AND sm.date <= %s"
            params.append(fecha_hasta)

        query += " GROUP BY sm.product_id"

        self._cr.execute(query, tuple(params))
        
        for row in self._cr.dictfetchall():
            template = template_by_variant.get(row['product_id'])
            if template:
                template.consumo_filtrado += row['total'] or 0.0

    def action_abrir_wizard_listado(self):
        return {
            'name': 'Filtrar Consumo por Rango',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.rango.lista',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_abrir_wizard_consumo(self):
        self.ensure_one()
        variant_id = self.product_variant_id.id if self.product_variant_id else False
        if not variant_id:
            return {}

        return {
            'name': 'Análisis de Consumo Personalizado',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.product.consumo',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': variant_id},
        }