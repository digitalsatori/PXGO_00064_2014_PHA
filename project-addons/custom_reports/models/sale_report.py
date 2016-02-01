# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    notified_partner_id = fields.Many2one('res.partner', 'Cooperative')
    sale_type = fields.Selection(selection=[('normal', 'Normal'),
                                            ('sample', 'Sample'),
                                            ('transfer', 'Transfer'),
                                            ('replacement', 'Replacement'),
                                            ('intermediary', 'Intermediary')],
                                 string="Type")
    sale_channel_id = fields.Many2one('sale.channel', 'Canal de venta')
    partner_category = fields.Char('Partner category')
    commission_category = fields.Char('Commission category')
    country_id = fields.Many2one('res.country', 'Invoicing country')

    def _select(self):
        select_str = """
            , s.notified_partner_id as notified_partner_id
            , s.sale_type as sale_type
            , s.sale_channel_id as sale_channel_id
            , (
                select
                    rpc.name
                from res_partner_res_partner_category_rel rpcr,
                     res_partner_category rpc
                where rpcr.partner_id = s.partner_id
                  and rpc.id = rpcr.category_id
                limit 1
            ) partner_category
            , (
                select
                    pc.name
                from product_categ_rel pcr, product_category pc, product_category cpc
                where pcr.product_id = p.id
                  and pc.id = pcr.categ_id
                  and cpc.id = pc.parent_id and cpc.commissions_parent_category = true
                limit 1
            ) commission_category
            , pa.country_id as country_id
            """
        return super(SaleReport, self)._select() + select_str

    def _from(self):
        from_str = """
            left join res_partner pa
                   on (pa.id = s.partner_id and pa.company_id = s.company_id)
            """
        return super(SaleReport, self)._from() + from_str

    def _group_by(self):
        group_by_str = """
            , s.notified_partner_id, s.sale_type, s.sale_channel_id
            , partner_category, commission_category, pa.country_id
            """
        return super(SaleReport, self)._group_by() + group_by_str
