# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class Ean10Code(models.Model):
    _name = 'ean10.code'

    name = fields.Char(required=True)

    @api.multi
    def _generate_and_search_ean13(self):
        def control_code13(code):
            sum = 0
            for d in range(12):
                sum += int(code[d]) * (1 if d % 2 == 0 else 3)
            return (10 - sum % 10) % 10

        # Reserved EAN for company
        reserved_ean = self.env.user.company_id.partner_id.gln

        # Search and delete all previously generated ean13 codes
        ean13_ids = self.env['ean13.product']
        for ean10 in self:
            ean13_ids |= ean13_ids.with_context(generating_ean13=True).\
                search([('name', '=like', ean10.name + '%')])
        if ean13_ids:
            ean13_ids.unlink()

        ean10_ean13_ids = self.env['ean13.product']
        # Generate all ean13 codes for each ean10
        for ean10 in self:
            ean13_ids = self.env['ean13.product']
            product_ids = self.env['product.product']

            for pair in range(100):
                control_digit = control_code13('{}{:02d}'.format(ean10.name, pair))
                ean13 = '{}{:02d}{:d}'.format(ean10.name, pair, control_digit)
                reserved = ean13 == reserved_ean
                product_ids = product_ids.\
                    search([('ean13', '=', ean13)])
                if product_ids:
                    for product_id in product_ids:
                        ean10_ean13_ids |= ean13_ids.create({
                            'name': ean13,
                            'product_id': product_id.id,
                            'default_code': product_id.default_code,
                            'country_id': product_id.country.id,
                            'uses': len(product_ids),
                            'reserved': reserved or product_id.type == 'service'
                        })
                else:
                    ean10_ean13_ids |= ean13_ids.create({
                        'name': ean13,
                        'product_id': False,
                        'default_code': self.env.user.company_id.name if reserved
                                                                      else False,
                        'country_id': False,
                        'uses': 1 if reserved else 0,
                        'reserved': reserved
                    })
        return ean10_ean13_ids

    @api.multi
    def generate_and_search_ean13(self):
        ean13_ids = self._generate_and_search_ean13()

        view_id = self.env.ref('ean10.ean13_tree_view')
        ctx = self.env.context.copy()
        ctx['viewing_from_ean10'] = True
        return {
            'name': _('EAN13 codes for %s') % self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'ean13.product',
            'view_id': view_id.id,
            'target': 'current',
            'domain': [('id', 'in', ean13_ids.ids)],
            'context': ctx,
        }


class Ean13Product(models.Model):
    _name = 'ean13.product'

    name = fields.Char(readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', readonly=True)
    default_code = fields.Char(readonly=True)
    country_id = fields.Many2one(comodel_name='res.country', readonly=True)
    uses = fields.Integer(readonly=True)
    reserved = fields.Boolean()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if not (self.env.context.get('viewing_from_ean10') or \
                self.env.context.get('generating_ean13')):
            ean13_ids = self.env['ean10.code'].search([]).\
                _generate_and_search_ean13()
            args = [('id', 'in', ean13_ids.ids)] + args
        return super(models.Model, self).search(args, offset=offset,
                                                limit=limit, order=order,
                                                count=count)


class Ean13International(models.Model):
    _name = 'ean13.international'

    name = fields.Char(readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', readonly=True)
    default_code = fields.Char(readonly=True)
    country_id = fields.Many2one(comodel_name='res.country', readonly=True)
    uses = fields.Integer(readonly=True)
    reserved = fields.Boolean()

    @api.model
    def _generate_and_search_ean13(self):
        # Reserved EAN for company
        reserved_ean = self.env.user.company_id.partner_id.gln

        ean13_ids = self.env['ean13.international'].\
            with_context(generating_ean13=True).search([])
        ean13_names = list(set(ean13_ids.mapped('name')))  # Avoid duplicates
        product_ids = self.env['product.product']

        ean13_ids.unlink()
        ean13_ids = self.env['ean13.international']

        for ean13 in ean13_names:
            reserved = ean13 == reserved_ean
            product_ids = product_ids.search([('ean13', '=', ean13)])
            if product_ids:
                for product_id in product_ids:
                    ean13_ids |= ean13_ids.with_context(generating_ean13=True).create({
                        'name': ean13,
                        'product_id': product_id.id,
                        'default_code': product_id.default_code,
                        'country_id': product_id.country.id,
                        'uses': len(product_ids),
                        'reserved': reserved or product_id.type == 'service'
                    })
            else:
                ean13_ids |= ean13_ids.with_context(generating_ean13=True).create({
                    'name': ean13,
                    'product_id': False,
                    'default_code': self.env.user.company_id.name if reserved
                                                                  else False,
                    'country_id': False,
                    'uses': 1 if reserved else 0,
                    'reserved': reserved
                })
        return ean13_ids

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if not self.env.context.get('generating_ean13'):
            ean13_ids = self._generate_and_search_ean13()
            args = [('id', 'in', ean13_ids.ids)] + args
        return super(models.Model, self).search(args, offset=offset,
                                                limit=limit, order=order,
                                                count=count)

    @api.model
    def create(self, vals):
        res = super(Ean13International, self).create(vals)
        if not self.env.context.get('generating_ean13'):
            self._generate_and_search_ean13()
        return res