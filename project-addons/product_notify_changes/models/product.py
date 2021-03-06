# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def write(self, vals):
        disable_notify_changes = self.env.context.get('disable_notify_changes',
                                                      False)
        if (not disable_notify_changes) and (len(vals) == 1) and \
                ('standard_price' in vals):
            disable_notify_changes = True

        if not disable_notify_changes:
            orig_values = {}
            attrs = self.fields_get()
            for product in self:
                orig_values[product.id] = {}
                for field in vals:
                    field_value = eval('product.' + field)
                    field_type = attrs[field]['type']
                    if field_type in ['one2many', 'many2one', 'many2many']:
                        orig_values[product.id][field] = u", ".join(
                            [x.display_name for x in field_value]
                        )
                    else:
                        orig_values[product.id][field] = field_value

        res = super(ProductProduct, self).write(vals)

        if disable_notify_changes:
            return res

        for product in self:
            fields = ''
            for field in vals:
                field_value = eval('product.' + field)
                field_type = attrs[field]['type']
                if field_type == 'binary':
                    new_value = _('(new binary data)') if field_value else False
                elif field_type in ['one2many', 'many2one', 'many2many']:
                    new_value = u", ".join(
                        [x.display_name for x in field_value]
                    )
                else:
                    new_value = field_value

                if field_type == 'binary':
                    orig_value = _('(old binary data)') if \
                        orig_values[product.id][field] else False
                else:
                    orig_value = orig_values[product.id][field]

                orig_value = orig_value if orig_value else _('(no data)')
                new_value = new_value if new_value else _('(no data)')
                fields += u'<br>{0}: {1} >> {2}'.format(
                        _(attrs[field]['string']), orig_value, new_value)

            product.message_post(body=_('Modified fields: ') + fields)

        return res
