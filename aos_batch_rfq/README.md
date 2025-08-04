# Batch RFQ Management

A comprehensive Odoo module for managing Request for Quotations (RFQs) in batches, similar to batch transfer concepts. This module streamlines the procurement process by allowing users to create, send, and manage multiple RFQs simultaneously.

## Features

### 🛒 Batch Processing
- Create and manage multiple RFQs in a single workflow
- Process vendor requests efficiently with batch operations
- Similar concept to batch transfers but for procurement

### 🎯 Smart Vendor Management
- Automatically distribute RFQs to multiple vendors
- Track vendor responses and quotations
- Compare quotations side by side
- Vendor response time tracking

### 📊 Progress Tracking
- Real-time progress monitoring with statistics
- Progress bars and status indicators
- Overdue RFQ tracking
- Comprehensive dashboard views

### 📧 Automated Communication
- Customizable email templates for vendor communication
- Bulk send RFQs to vendors
- Automated follow-up capabilities
- Integration with Odoo's mail system

### 📈 Analytics & Reporting
- Comprehensive reporting with pivot tables and graphs
- Price variance analysis
- Vendor performance metrics
- Response time analytics

### ⚙️ Flexible Creation Methods
- **Manual Entry**: Create RFQ lines manually
- **From Products**: Select products and vendors automatically
- **From Templates**: Use predefined templates for recurring needs
- **From Purchase Requests**: Integration with purchase request workflows

## Installation

1. Copy the `aos_batch_rfq` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "Batch RFQ Management" module
4. Configure user permissions as needed

## Dependencies

- `base` - Odoo base module
- `purchase` - Purchase management
- `stock` - Inventory management
- `sale_management` - Sales management
- `account` - Accounting
- `report_xlsx` - Excel reporting

## Usage

### Creating a Batch RFQ

1. **Navigate to Batch RFQ > Operations > Batch RFQs**
2. **Click "Create" or use the wizard for guided creation**
3. **Choose your creation method**:
   - Manual: Add lines manually
   - From Products: Select products and vendors
   - From Template: Use predefined templates
4. **Configure settings** (deadline, priority, email template)
5. **Confirm the batch RFQ**

### Processing Workflow

1. **Generate RFQs**: Create individual purchase orders for each vendor
2. **Send to Vendors**: Bulk send RFQs using email templates
3. **Track Responses**: Monitor vendor responses and update quotations
4. **Compare & Select**: Analyze quotations and select best offers
5. **Generate Reports**: Analyze performance and results

### Key Models

- **Batch RFQ** (`batch.rfq`): Main batch RFQ management
- **Batch RFQ Line** (`batch.rfq.line`): Individual RFQ lines
- **Purchase Category** (`purchase.category`): Categorization system
- **Batch RFQ Template** (`batch.rfq.template`): Reusable templates
- **Batch RFQ Report** (`batch.rfq.report`): Analytics and reporting

### Views Available

- **Kanban View**: Visual progress tracking
- **Tree View**: List view with filters and sorting
- **Form View**: Detailed batch RFQ management
- **Pivot View**: Analytics and reporting
- **Graph View**: Visual analytics

## Configuration

### Security Groups

- **Batch RFQ User**: Basic access to create and manage batch RFQs
- **Batch RFQ Manager**: Full access including templates and configuration

### Email Templates

The module includes a default email template for RFQ communication. You can:
- Customize the existing template
- Create additional templates for different scenarios
- Use dynamic content based on batch RFQ data

### Categories

Create purchase categories to organize your batch RFQs:
1. Go to Batch RFQ > Configuration > Purchase Categories
2. Create categories with codes and descriptions
3. Use categories for filtering and reporting

## Technical Details

### Database Structure

The module uses proper Odoo ORM with:
- Computed fields for statistics and progress
- Proper constraints and validations
- Multi-company support
- Audit trail with mail threading

### Integration Points

- **Purchase Module**: Extends purchase orders with batch RFQ references
- **Mail System**: Integrated email communication
- **Reporting**: Custom reports and analytics
- **Security**: Proper access controls and record rules

### Customization

The module is designed for easy customization:
- Extend models with additional fields
- Add custom workflows and automations
- Create specialized reports
- Integrate with other modules

## API Examples

### Creating a Batch RFQ Programmatically

```python
# Create a batch RFQ
batch_rfq = self.env['batch.rfq'].create({
    'description': 'Monthly Office Supplies',
    'date_deadline': fields.Datetime.now() + timedelta(days=7),
    'category_id': category_id,
    'priority': '2',
})

# Add lines
self.env['batch.rfq.line'].create({
    'batch_rfq_id': batch_rfq.id,
    'name': 'A4 Paper',
    'partner_id': vendor_id,
    'product_id': product_id,
    'product_qty': 10,
    'product_uom_id': uom_id,
    'estimated_price': 5.00,
})

# Confirm and process
batch_rfq.action_confirm()
batch_rfq.action_generate_rfqs()
batch_rfq.action_send_rfqs()
```

### Searching and Filtering

```python
# Find overdue batch RFQs
overdue_rfqs = self.env['batch.rfq'].search([
    ('date_deadline', '<', fields.Datetime.now()),
    ('state', 'not in', ['done', 'cancelled'])
])

# Get batch RFQs with high price variance
high_variance = self.env['batch.rfq.report'].search([
    ('price_variance', '>', 10)
])
```

## Support and Maintenance

### Scheduled Actions

The module includes a scheduled action to automatically update batch RFQ statuses based on progress. This runs daily and updates:
- Batch RFQs from 'sent' to 'partial' when some responses are received
- Batch RFQs from 'partial' to 'done' when all responses are received

### Maintenance Tasks

- Regular cleanup of old wizard records
- Archive completed batch RFQs after specified period
- Monitor and optimize database views for reporting

## Troubleshooting

### Common Issues

1. **RFQs not generating**: Check vendor configuration and product settings
2. **Emails not sending**: Verify email template and SMTP configuration
3. **Progress not updating**: Run the scheduled action manually or check cron jobs
4. **Permission errors**: Verify user groups and access rights

### Debug Mode

Enable developer mode to access:
- Technical menu items
- Database view inspection
- Advanced filtering options
- Model field information

## License

This module is licensed under LGPL-3.

## Author

La Jayuhni Yarsyah

## Version History

- **1.0.0**: Initial release with core batch RFQ functionality
- Features: Batch creation, vendor management, progress tracking, reporting

---

For more information or support, please refer to the module documentation or contact the development team.