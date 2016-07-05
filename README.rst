********************************************
Hibou - US Payroll Calculations & Accounting
********************************************

Provides a basis for setting up a US class of employee for Odoo Payroll. For more information and add-ons, visit `Hibou.io <https://hibou.io/>`_.

`Inspired by Odoo l10n_be_hr_payroll and l10n_be_hr_payroll_account localizations`


=============
Main Features
=============

* Social Security and Medicare withholding (collectively FICA) (with caps)
* Additional Medicare calculation
* Friendly separation between Employee and Company Contributions
* Federal Unemployment withholding (FUTA) (with caps)
* Federal Income Tax Withholding
* Contribution Registers and Contacts to ease paying and filing forms 940 and 941
* Unit tested rules and rates for 2016 from IRS Publication 15 (Circular E)
* External Wages field on Employee Contract for switching to Odoo mid-year. (e.g. FUTA wages YTD)

===
Use
===

In general, the base module (l10n_us_hr_payroll) should form the basis for a 'US Employee' Salary Structure (that would be the
parent of a state specific Salary Structure if need be). This module provides all of the Salary Rules (calculations), registers,
and Partners (e.g. EFTPS).

The secondary module (l10n_us_hr_payroll_account) is a very basic mapping between the stock Odoo US Chart of Accounts and the
various Salary Rules from above. These mappings are very generic and probably not appropriate for general use, and is meant for
testing or inspiration. (Odoo's Chart of Accounts lacks specific accounts for things like `Employee Net Payable`, and I suggest
that you create your own!)


=======
Licence
=======

Please see `LICENSE <https://github.com/hibou-io/odoo-us-payroll/blob/master/LICENSE>`_.

Copyright Hibou Corp. 2016.