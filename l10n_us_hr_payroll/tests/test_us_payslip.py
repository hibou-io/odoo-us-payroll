# -*- coding: utf-8 -*-

from logging import getLogger
from sys import float_info

from openerp.tests import common
from openerp.tools.float_utils import float_round

DEBUG = False
_logger = getLogger(__name__)


class TestUsPayslip(common.TransactionCase):
    _payroll_digits = -1

    @property
    def payroll_digits(self):
        if self._payroll_digits == -1:
            self._payroll_digits = self.env['decimal.precision'].precision_get('Payroll')
        return self._payroll_digits

    def _log(self, message):
        if DEBUG:
            _logger.warn(message)
            
    def _createEmployee(self):
        return self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared'
        })

    def _createContract(self, employee, salary, schedule_pay='monthly', w4_allowances=0, w4_filing_status='single'):
        return self.env['hr.contract'].create({
            'date_start': '2016-01-01',
            'date_end': '2016-12-31',
            'name': 'Contract for Jared 2016',
            'wage': salary,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'employee_id': employee.id,
            'struct_id': self.ref('l10n_us_hr_payroll.hr_payroll_salary_structure_us_employee'),
            'working_hours': self.ref('resource.timesheet_group1'),
            'schedule_pay': schedule_pay,
            'w4_allowances': w4_allowances,
            'w4_filing_status': w4_filing_status
        })

    def _createPayslip(self, employee, date_from, date_to):
        return self.env['hr.payslip'].create({
            'employee_id': employee.id,
            'date_from': date_from,
            'date_to': date_to
        })

    def _getCategories(self, payslip):
        detail_lines = payslip.details_by_salary_rule_category
        categories = {}
        for line in detail_lines:
            self._log(' line code: ' + str(line.code) +
                      ' category code: ' + line.category_id.code +
                      ' total: ' + str(line.total) +
                      ' rate: ' + str(line.rate) +
                      ' amount: ' + str(line.amount))
            if line.category_id.code not in categories:
                categories[line.category_id.code] = line.total
            else:
                categories[line.category_id.code] += line.total

        return categories

    def assertPayrollEqual(self, first, second):
        self.assertAlmostEqual(first, second, self.payroll_digits)

    ###
    #   2016 Taxes and Rates
    ###

    def test_2016_taxes(self):
        # salary is high so that second payslip runs over max
        # social security salary
        salary = 80000.0;

        ## tax rates
        FICA_SS = -0.062
        FICA_M = -0.0145
        FUTA = -0.06
        FICA_M_ADD = -0.009

        ## tax maximums
        FICA_SS_MAX_WAGE = 118500.0
        FICA_M_MAX_WAGE = float_info.max
        FICA_M_ADD_START_WAGE = 200000.0
        FUTA_MAX_WAGE = 7000.0


        employee = self._createEmployee()

        contract = self._createContract(employee, salary)

        self._log('2016 tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], FUTA_MAX_WAGE)
        self.assertPayrollEqual(cats['FUTA'], cats['FUTA_WAGES'] * FUTA)

        payslip.process_sheet()

        # Make a new payslip, this one will have maximums for FICA Social Security Wages

        remaining_ss_wages = FICA_SS_MAX_WAGE - salary if (FICA_SS_MAX_WAGE - 2*salary < salary) else salary
        remaining_m_wages = FICA_M_MAX_WAGE - salary if (FICA_M_MAX_WAGE - 2*salary < salary) else salary

        self._log('2016 tax second payslip:')
        payslip = self._createPayslip(employee, '2016-02-01', '2016-02-29')  # 2016 is a leap year

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], remaining_ss_wages)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], remaining_m_wages)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], 0)
        self.assertPayrollEqual(cats['FUTA'], 0)

        payslip.process_sheet()

        # Make a new payslip, this one will have reached Medicare Additional (employee only)

        self._log('2016 tax third payslip:')
        payslip = self._createPayslip(employee, '2016-03-01', '2016-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], FICA_M_ADD_START_WAGE - (salary * 2))  # aka 40k
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * FICA_M_ADD)

        payslip.process_sheet()

        # Make a new payslip, this one will have all salary as Medicare Additional

        self._log('2016 tax fourth payslip:')
        payslip = self._createPayslip(employee, '2016-04-01', '2016-04-30')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * FICA_M_ADD)

        payslip.process_sheet()

    def test_2016_fed_income_withholding_single(self):
        salary = 6000.00
        schedule_pay = 'monthly'
        w4_allowances = 3
        w4_allowance_amt = 337.50 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 4987.50, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = float_round(-(431.95 + ((adjusted_salary - 3325) * 0.25)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'single')

        self._log('2016 fed income single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)

    def test_2016_fed_income_withholding_married_as_single(self):
        salary = 500.00
        schedule_pay = 'weekly'
        w4_allowances = 1
        w4_allowance_amt = 77.90 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 422.10, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = float_round(-(17.90 + ((adjusted_salary - 222) * 0.15)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'married_as_single')

        self._log('2016 fed income married_as_single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)

    def test_2016_fed_income_withholding_married(self):
        salary = 14000.00
        schedule_pay = 'bi-weekly'
        w4_allowances = 2
        w4_allowance_amt = 155.80 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 1368.84, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = float_round(-(1992.05 + ((adjusted_salary - 9231) * 0.33)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'married')

        self._log('2016 fed income married payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)