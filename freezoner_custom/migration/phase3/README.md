# Freezoner Phase 3 Migration

This module contains the migrated customizations for Freezoner to Odoo 18, focusing on core business models and their interactions.

## Overview

The Phase 3 migration includes the following key models:
- Task Management (`task.py`)
- Sale Order Management (`sale.py`)
- Statement of Values (`sov.py`)

## Model Details

### 1. Task Model (`task.py`)
Enhanced project task management with:
- Document management integration
- Payment state tracking
- Advanced stage management
- Email notification system
- Batch operations support

Key Features:
- Document attachment handling
- Payment state tracking
- Stage-based workflow
- Email notifications
- Batch create/write operations

### 2. Sale Order Model (`sale.py`)
Extended sale order functionality with:
- System expiry date management
- Advanced payment tracking
- Partner validation
- Revenue and expense tracking
- Batch operations support

Key Features:
- Automatic expiration handling
- Payment method tracking
- Partner validation (company/individual)
- Revenue and expense calculations
- Batch create/write operations

### 3. Statement of Values Model (`sov.py`)
New model for financial tracking with:
- Revenue and expense management
- Profit margin calculations
- Analytic line integration
- State management
- Batch operations support

Key Features:
- Revenue and planned expenses tracking
- Net achievement calculations
- Actual expenses from analytic lines
- Profit margin computation
- State workflow (draft → in progress → done)
- Analytic line integration

## Technical Details

### Dependencies
```python
'depends': [
    'base',
    'project',
    'sale',
    'sale_project',
    'account',
    'analytic',
    'mail',
    'web',
    'client_documents',
]
```

### Security
Access rights are defined for:
- Basic users (read/write/create)
- Sales managers (full access)
- Accountants (read/write/create)
- Accounting managers (full access)

### Views
Each model has dedicated views:
- Tree views with status decorations
- Form views with smart buttons
- Search views with filters and grouping
- Action windows with help messages

## Installation

1. Ensure all dependencies are installed:
   ```bash
   ./odoo-bin -c odoo.conf -d your_database -i base,project,sale,sale_project,account,analytic,mail,web,client_documents --stop-after-init
   ```

2. Install the migration module:
   ```bash
   ./odoo-bin -c odoo.conf -d your_database -i migration_phase3 --stop-after-init
   ```

## Upgrade Process

1. Backup your database
2. Update the module list
3. Upgrade the module:
   ```bash
   ./odoo-bin -c odoo.conf -d your_database -u migration_phase3 --stop-after-init
   ```

## Key Changes from Previous Version

1. Task Model:
   - Added batch operations support
   - Enhanced document management
   - Improved stage workflow
   - Updated email notification system

2. Sale Order Model:
   - Added batch operations support
   - Enhanced partner validation
   - Improved expiration handling
   - Updated payment tracking

3. Statement of Values Model:
   - New model for financial tracking
   - Analytic line integration
   - State-based workflow
   - Batch operations support

## Testing

After installation, verify:
1. Task creation and stage transitions
2. Sale order creation with partner validation
3. SOV creation and financial calculations
4. Document attachments
5. Email notifications
6. Access rights for different user groups

## Troubleshooting

Common issues and solutions:

1. Model not found errors:
   - Verify all dependencies are installed
   - Check module installation order
   - Clear browser cache

2. Access rights issues:
   - Verify user group assignments
   - Check security rules
   - Review access rights CSV

3. Computation errors:
   - Verify analytic account setup
   - Check related field dependencies
   - Review computation methods

## Support

For issues or questions:
1. Check the error logs
2. Review the model documentation
3. Contact the development team

## License

This module is licensed under LGPL-3. 