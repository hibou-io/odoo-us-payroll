from openerp import models, fields


class USHrContract(models.Model):
    _inherit = 'hr.contract'

    w4_allowances = fields.Integer(string='Federal W4 Allowances')
    w4_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('married_as_single', 'Married but at Single Rate'),
    ], string='Federal W4 Filing Status')

    external_wages = fields.Float(string='External Existing Wages')
