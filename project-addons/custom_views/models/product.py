# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp
import datetime


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_in_current_pricelist = fields.Boolean(
        compute='_compute_is_in_current_pricelist',
        search='_search_is_in_current_pricelist')
    year_appearance = fields.Integer('Year of appearance',
        default=datetime.datetime.now().year)
    manufacturing_procedure_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'product_manufacturing')]",
        string='Manufacturing procedure')
    manufacturing_procedure_attachment = fields.Binary(
        related='manufacturing_procedure_id.attachment')
    manufacturing_procedure_filename = fields.Char(
        related='manufacturing_procedure_id.attachment_filename')
    packaging_procedure_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'product_packaging')]",
        string='Packaging procedure')
    packaging_procedure_attachment = fields.Binary(
        related='packaging_procedure_id.attachment')
    packaging_procedure_filename = fields.Char(
        related='packaging_procedure_id.attachment_filename')
    specification_type = fields.Many2one(comodel_name='mrp.procedure.type',
        domain="[('code', 'ilike', 'specifications%')]",
        string='Specification type')
    specification_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id', '=', specification_type)]",
        string='Specification')
    specification_attachment = fields.Binary(
        related='specification_id.attachment')
    specification_filename = fields.Char(
        related='specification_id.attachment_filename')
    analysis_method_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'quality_control_analysis_methods')]",
        string='Analysis method')
    analysis_method_attachment = fields.Binary(
        related='analysis_method_id.attachment')
    analysis_method_filename = fields.Char(
        related='analysis_method_id.attachment_filename')
    analysis_plan_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'quality_control_analysis_plans')]",
        string='Analysis plan')
    analysis_plan_attachment = fields.Binary(
        related='analysis_plan_id.attachment')
    analysis_plan_filename = fields.Char(
        related='analysis_plan_id.attachment_filename')

    @api.one
    @api.constrains('year_appearance')
    def _check_year_of_appearance(self):
        current_year = datetime.datetime.now().year
        if 1956 >= self.year_appearance <= current_year:
            raise Warning(_('Year must be between 1956 and %s.') %
                          (current_year,))

    @api.multi
    def name_get(self):  # Hide default_code by default
        return super(ProductProduct,
                     self.with_context(display_default_code=False)).name_get()

    @api.depends('pricelist_id')
    def _compute_is_in_current_pricelist(self):
        pricelist = self.pricelist_id.mapped('id')
        return self.env.context.get('pricelist', False) in pricelist

    def _search_is_in_current_pricelist(self, operator, value):
        # This domain filter by price list is only for Pharmadus and
        # sale orders that aren't for sample/advertising purposes
        if (self.env.user.company_id != self.env.ref('base.main_company')) or\
                self.env.context.get('is_a_sample_order', False):
            return [('active', '=', True)]

        current_pricelist_product_list = []
        pricelist = self.env.context.get('pricelist', False)
        if pricelist:
            pricelist_id = self.env['product.pricelist'].browse(pricelist)
            current_pricelist_product_list = \
                pricelist_id.version_id.items_id.mapped('product_id.id')
        if ((operator == '=') and value) or ((operator == '!=') and not value):
            operator = 'in'
        else:
            operator = 'not in'
        return [('id', operator, current_pricelist_product_list)]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    suppliers_pricelists = fields.One2many('pricelist.partnerinfo',
                                 compute='_suppliers_pricelists')
    cost_price_rm = fields.Float('Raw material cost price',
                                 digits=dp.get_precision('Product Price'))
    cost_price_components = fields.Float('Components cost price',
                                 digits=dp.get_precision('Product Price'))
    cost_price_dl = fields.Float('Direct labor cost price',
                                 digits=dp.get_precision('Product Price'))
    internal_scrapped_qty = fields.Float('Stock at internal scrap location',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly = True)
    virtual_conservative = fields.Float('Virtual stock conservative',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)
    out_of_existences = fields.Float('Out of existences',
                             digits=dp.get_precision('Product Unit of Measure'),
                             readonly=True)
    real_incoming_qty = fields.Float('Real incoming qty.',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)
    production_planning_qty = fields.Float(
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)
    stock_move_ids = fields.One2many(string='Stock movements',
                                     comodel_name='stock.move',
                                     inverse_name='product_id')

    @api.one
    @api.depends('seller_ids')
    def _suppliers_pricelists(self):
        ids = []
        for product in self:
            for seller in product.seller_ids:
                for pricelist in seller.pricelist_ids:
                    ids.append(pricelist.id)
        self.suppliers_pricelists = ids

    @api.multi
    def compute_detailed_stock(self):
        warehouses = self.env['stock.warehouse'].search([])
        stock_ids = [wh.lot_stock_id.id for wh in warehouses]

        for product in self:
            if not product.product_variant_ids:
                continue

            product_id = product.product_variant_ids[0]

            quants = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id.usage', '=', 'internal'),
                ('location_id.scrap_location', '=', True)
            ])
            internal_scrapped_qty = sum(quant.qty for quant in quants)

            quants = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id.id', '=', 21)  # Hoard location
            ])
            hoard_qty = sum(quant.qty for quant in quants)
            virtual_conservative = product.qty_available - hoard_qty - \
                                   product.outgoing_qty - internal_scrapped_qty

            production_planning_orders = self.env['production.planning.orders'].\
                search([('product_id', '=', product_id.id)])
            production_planning_qty = sum(order.product_qty for order in
                                          production_planning_orders)

            quants = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id.usage', '=', 'internal'),
                ('location_id.scrap_location', '=', False),
                '!', ('location_id', 'child_of', stock_ids)
            ])
            out_of_existences = sum(quant.qty for quant in quants)

            moves = self.env['stock.move'].search([
                ('product_id', '=', product_id.id),
                ('state', 'in', ('assigned', 'confirmed', 'waiting')),
                ('picking_id.picking_type_id.code', '=', 'incoming'),
                ('location_id.usage', '!=', 'internal'),
                ('location_dest_id.usage', '=', 'internal')
            ])
            real_incoming_qty = sum(move.product_uom_qty for move in moves)

            product.write({
                'internal_scrapped_qty': internal_scrapped_qty,
                'virtual_conservative': virtual_conservative,
                'production_planning_qty': production_planning_qty,
                'out_of_existences': out_of_existences,
                'real_incoming_qty': real_incoming_qty})

            product_id._production_qty()  # Update qty in production if required


class PricelistPartnerinfo(models.Model):
    _inherit = 'pricelist.partnerinfo'

    sequence = fields.Integer(related='suppinfo_id.sequence')