from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta

class WizardProductConsumo(models.TransientModel):
    _name = 'wizard.product.consumo'
    _description = 'Asistente de Análisis de Consumo'

    product_id = fields.Many2one('product.product', string="Producto", required=True)
    
    # Filtros personalizados por el usuario
    fecha_desde = fields.Date(string="Fecha Desde")
    fecha_hasta = fields.Date(string="Fecha Hasta")

    # Fechas Extremas de Consumo (Informativas)
    fecha_primer_consumo = fields.Date(string="Primer Consumo", readonly=True)
    fecha_ultimo_consumo = fields.Date(string="Último Consumo", readonly=True)

    # Resultados de los Períodos
    consumo_3_meses = fields.Float(string="Últimos 3 Meses", readonly=True)
    consumo_1_ano = fields.Float(string="Último Año", readonly=True)
    consumo_3_anos = fields.Float(string="Últimos 3 Años", readonly=True)
    consumo_historico = fields.Float(string="Consumo Histórico Total", readonly=True)
    consumo_personalizado = fields.Float(string="Rango Personalizado", readonly=True)

    @api.model
    def default_get(self, fields_list):
        """ Al abrirse el wizard, calcula automáticamente todos los períodos fijos """
        res = super(WizardProductConsumo, self).default_get(fields_list)
        if 'product_id' in res or self._context.get('default_product_id'):
            prod_id = res.get('product_id') or self._context.get('default_product_id')
            
            # Pasamos estrictamente None en lugar de False para evitar el error de tipado en SQL
            vals = self._calcular_radiografia_consumo(prod_id, fecha_d=None, fecha_h=None)
            res.update(vals)
        return res

    def action_calcular_consumo(self):
        """ Acción del botón 'Calcular Rango Personalizado' dentro del wizard """
        self.ensure_one()
        # Si los campos del formulario están vacíos, Odoo devuelve False. Los convertimos a None.
        f_desde = self.fecha_desde if self.fecha_desde else None
        f_hasta = self.fecha_hasta if self.fecha_hasta else None
        
        vals = self._calcular_radiografia_consumo(self.product_id.id, f_desde, f_hasta)
        self.write(vals)
        
        # Retornamos el mismo wizard para que muestre los resultados dinámicos actualizados
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _calcular_radiografia_consumo(self, product_id, fecha_d=None, fecha_h=None):
        """ Consulta SQL única de alto rendimiento para extraer todos los períodos y fechas clave """
        hoy = date.today()
        f_3m = hoy - relativedelta(months=3)
        f_1a = hoy - relativedelta(years=1)
        f_3a = hoy - relativedelta(years=3)

        query = """
            SELECT 
                MIN(sm.date)::date as primer_consumo,
                MAX(sm.date)::date as ultimo_consumo,
                
                SUM(CASE WHEN sm.date >= %s THEN 
                    (CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty
                          WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END)
                    ELSE 0 END) as c_3m,
                    
                SUM(CASE WHEN sm.date >= %s THEN 
                    (CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty
                          WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END)
                    ELSE 0 END) as c_1a,
                    
                SUM(CASE WHEN sm.date >= %s THEN 
                    (CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty
                          WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END)
                    ELSE 0 END) as c_3a,
                    
                SUM(CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty
                         WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END) as c_hist,
                         
                SUM(CASE WHEN (%s::date IS NOT NULL AND %s::date IS NOT NULL AND sm.date::date BETWEEN %s AND %s) THEN 
                    (CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' THEN sm.product_qty
                          WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' THEN -sm.product_qty ELSE 0 END)
                    ELSE 0 END) as c_custom
            FROM stock_move sm
            JOIN stock_location src_loc ON sm.location_id = src_loc.id
            JOIN stock_location dest_loc ON sm.location_dest_id = dest_loc.id
            WHERE sm.state = 'done' AND sm.product_id = %s
        """
        
        # Parámetros ordenados para el query de PostgreSQL
        params = (f_3m, f_1a, f_3a, fecha_d, fecha_h, fecha_d, fecha_h, product_id)
        self.env.cr.execute(query, params)
        res = self.env.cr.dictfetchone()

        if res:
            return {
                'fecha_primer_consumo': res.get('primer_consumo'),
                'fecha_ultimo_consumo': res.get('ultimo_consumo'),
                'consumo_3_meses': res.get('c_3m') or 0.0,
                'consumo_1_ano': res.get('c_1a') or 0.0,
                'consumo_3_anos': res.get('c_3a') or 0.0,
                'consumo_historico': res.get('c_hist') or 0.0,
                'consumo_personalizado': res.get('c_custom') or 0.0 if (fecha_d and fecha_h) else 0.0
            }
        return {}