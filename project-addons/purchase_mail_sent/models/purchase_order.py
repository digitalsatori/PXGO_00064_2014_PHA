# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Marcos Ybarra <marcos.ybarra@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields, osv

class purchase_order(orm.Model):
    _inherit = 'purchase.order'
    _description = "Check inf PC mail has been sent"
    _columns = {
        'pc_sent': fields.boolean('¿PC Sent?'),
    }
    _defaults = {
        'pc_sent' : False,
    }