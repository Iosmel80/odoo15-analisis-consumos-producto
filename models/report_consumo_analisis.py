from odoo import models, fields, api, tools

class ReportConsumoAnalisis(models.Model):
    _name = 'report.consumo.analisis'
    _description = 'Análisis de Consumo por Producto'
    _auto = False
    _order = 'default_code asc'

    # Campos nativos del producto
    product_id = fields.Many2one('product.product', string='DESCRIPCIÓN', readonly=True)
    default_code = fields.Char(string='Código', readonly=True)
    name = fields.Char(string='Nombre', readonly=True)
    description_purchase = fields.Text(string='TEXTO_COMPRA', readonly=True)
    uom_id = fields.Many2one('uom.uom', string='UM', readonly=True)
    categ_id = fields.Many2one('product.category', string='CATEGORIA', readonly=True)
    
    create_date = fields.Datetime(string='F_ALTA', readonly=True)
    create_uid = fields.Many2one('res.users', string='Creado Por', readonly=True)
    
    # Campos de Consumo
    consumo_3_meses = fields.Float(string='Consumo (3 Meses)', readonly=True)
    consumo_1_ano = fields.Float(string='Consumo (1 Año)', readonly=True)
    consumo_3_anos = fields.Float(string='Consumo (3 Años)', readonly=True)
    consumo_historico = fields.Float(string='Consumo Histórico', readonly=True)
    
    # === PRECIO PROMEDIO (AVCO) ===
    standard_price = fields.Float(
        string='Precio Promedio',
        readonly=True,
        digits='Product Price',
        related='product_id.standard_price',
        store=False
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Almacén',
        readonly=True,
    )
    quantity = fields.Float(
        string='Existencia',
        readonly=True,
    )
    total_quantity = fields.Float(
        string='Existencia Total',
        readonly=True,
    )
    total_pending_receipt = fields.Float(
        string='Total Pendiente de Recepción',
        readonly=True,
    )
    pending_order_quantity = fields.Float(
        string='Cantidad Pendiente en Pedido',
        readonly=True,
    )
    purchase_order_name = fields.Char(
        string='Pedido de Compra',
        readonly=True,
    )
    purchase_order_state = fields.Char(
        string='Estado del Pedido',
        readonly=True,
    )
    min_quantity = fields.Float(
        string='Cantidad Mínima',
        readonly=True,
        compute='_compute_reorder_quantities',
        store=False,
    )
    max_quantity = fields.Float(
        string='Cantidad Máxima',
        readonly=True,
        compute='_compute_reorder_quantities',
        store=False,
    )

    @api.depends('product_id')
    def _compute_reorder_quantities(self):
        for record in self:
            record.min_quantity = record.product_id.reordering_min_qty if record.product_id else 0.0
            record.max_quantity = record.product_id.reordering_max_qty if record.product_id else 0.0

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH move_summary AS (
                    SELECT
                        sm.product_id,
                        SUM(CASE WHEN sm.date >= NOW() - INTERVAL '3 months' 
                                  AND src_loc.usage = 'internal' AND dest_loc.usage = 'customer' 
                             THEN sm.product_qty
                             WHEN sm.date >= NOW() - INTERVAL '3 months' 
                                  AND src_loc.usage = 'customer' AND dest_loc.usage = 'internal' 
                             THEN -sm.product_qty
                             ELSE 0 END) AS c_3m,

                        SUM(CASE WHEN sm.date >= NOW() - INTERVAL '1 year' 
                                  AND src_loc.usage = 'internal' AND dest_loc.usage = 'customer' 
                             THEN sm.product_qty
                             WHEN sm.date >= NOW() - INTERVAL '1 year' 
                                  AND src_loc.usage = 'customer' AND dest_loc.usage = 'internal' 
                             THEN -sm.product_qty
                             ELSE 0 END) AS c_1y,

                        SUM(CASE WHEN sm.date >= NOW() - INTERVAL '3 years' 
                                  AND src_loc.usage = 'internal' AND dest_loc.usage = 'customer' 
                             THEN sm.product_qty
                             WHEN sm.date >= NOW() - INTERVAL '3 years' 
                                  AND src_loc.usage = 'customer' AND dest_loc.usage = 'internal' 
                             THEN -sm.product_qty
                             ELSE 0 END) AS c_3y,

                        SUM(CASE WHEN src_loc.usage = 'internal' AND dest_loc.usage = 'customer' 
                             THEN sm.product_qty
                             WHEN src_loc.usage = 'customer' AND dest_loc.usage = 'internal' 
                             THEN -sm.product_qty
                             ELSE 0 END) AS c_hist
                    FROM stock_move sm
                    JOIN stock_location src_loc ON sm.location_id = src_loc.id
                    JOIN stock_location dest_loc ON sm.location_dest_id = dest_loc.id
                    WHERE sm.state = 'done'
                    GROUP BY sm.product_id
                ),
                warehouse_stock AS (
                    SELECT
                        sq.product_id,
                        sw.id AS warehouse_id,
                        SUM(sq.quantity) AS quantity
                    FROM stock_quant sq
                    JOIN stock_location loc ON sq.location_id = loc.id
                    JOIN stock_warehouse sw ON loc.parent_path LIKE concat('%%/', sw.view_location_id, '/%%')
                    WHERE sq.quantity > 0
                        AND loc.usage = 'internal'
                    GROUP BY sq.product_id, sw.id
                ),
                warehouse_consumption AS (
                    SELECT DISTINCT
                        sm.product_id,
                        sw.id AS warehouse_id
                    FROM stock_move sm
                    JOIN stock_location src_loc ON sm.location_id = src_loc.id
                    JOIN stock_location dest_loc ON sm.location_dest_id = dest_loc.id
                    JOIN stock_warehouse sw ON src_loc.parent_path LIKE concat('%%/', sw.view_location_id, '/%%')
                    WHERE sm.state = 'done'
                        AND src_loc.usage = 'internal'
                        AND dest_loc.usage = 'customer'
                ),
                total_stock AS (
                    SELECT
                        sq.product_id,
                        SUM(sq.quantity) AS total_quantity
                    FROM stock_quant sq
                    JOIN stock_location loc ON sq.location_id = loc.id
                    WHERE sq.quantity > 0
                        AND loc.usage = 'internal'
                    GROUP BY sq.product_id
                ),
                purchase_pending AS (
                    SELECT
                        pol.product_id,
                        pol.order_id,
                        GREATEST(pol.product_qty - pol.qty_received, 0.0) AS pending_order_quantity
                    FROM purchase_order_line pol
                    JOIN purchase_order po ON pol.order_id = po.id
                    WHERE po.state != 'cancel'
                        AND pol.product_qty > pol.qty_received
                ),
                total_purchase_pending AS (
                    SELECT
                        product_id,
                        SUM(pending_order_quantity) AS total_pending_receipt
                    FROM purchase_pending
                    GROUP BY product_id
                ),
                warehouse_list AS (
                    SELECT product_id, warehouse_id, SUM(quantity) AS quantity
                    FROM (
                        SELECT product_id, warehouse_id, quantity FROM warehouse_stock
                        UNION ALL
                        SELECT product_id, warehouse_id, 0.0 AS quantity FROM warehouse_consumption
                    ) AS all_warehouses
                    GROUP BY product_id, warehouse_id
                )
                SELECT
                    row_number() OVER (ORDER BY pp.id, wl.warehouse_id) AS id,
                    pp.id AS product_id,
                    wl.warehouse_id AS warehouse_id,
                    COALESCE(wl.quantity, 0) AS quantity,
                    COALESCE(ts.total_quantity, 0) AS total_quantity,
                    COALESCE(tp.total_pending_receipt, 0) AS total_pending_receipt,
                    COALESCE(ppd.pending_order_quantity, 0) AS pending_order_quantity,
                    po.name AS purchase_order_name,
                    po.state AS purchase_order_state,
                    pp.default_code AS default_code,
                    pt.name AS name,
                    pt.description_purchase AS description_purchase,
                    pt.uom_id AS uom_id,
                    pt.categ_id AS categ_id,
                    pt.create_date AS create_date,
                    pt.create_uid AS create_uid,
                    COALESCE(ms.c_3m, 0) AS consumo_3_meses,
                    COALESCE(ms.c_1y, 0) AS consumo_1_ano,
                    COALESCE(ms.c_3y, 0) AS consumo_3_anos,
                    COALESCE(ms.c_hist, 0) AS consumo_historico
                FROM product_product pp
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN warehouse_list wl ON pp.id = wl.product_id
                LEFT JOIN move_summary ms ON pp.id = ms.product_id
                LEFT JOIN total_stock ts ON pp.id = ts.product_id
                LEFT JOIN total_purchase_pending tp ON pp.id = tp.product_id
                LEFT JOIN purchase_pending ppd ON pp.id = ppd.product_id
                LEFT JOIN purchase_order po ON ppd.order_id = po.id
            )
        """ % self._table)