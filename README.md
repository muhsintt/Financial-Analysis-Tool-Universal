# Expense Tracker - Financial Analysis Software

A comprehensive, fully-functional expense tracking and budget management application built with Python Flask and modern web technologies.

## Features

✅ **Dashboard** - Visual overview with income, expense, and net balance statistics
✅ **Transaction Management** - Add, edit, delete, and categorize all transactions
✅ **Budget Tracking** - Create budgets by category with daily/weekly/monthly/annual views
✅ **File Upload** - Import bank statements from CSV and Excel files
✅ **Auto-Categorization** - Automatic category detection for imported transactions
✅ **Reporting & Analytics** - Comprehensive reports with charts and trends
✅ **Expense Exclusion** - Exclude transactions from reports and budgets
✅ **Local Database** - SQLite for secure local data storage
✅ **Responsive Design** - Works on desktop, tablet, and mobile devices

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **RAM**: 512MB minimum
- **Disk Space**: 100MB minimum
- **Browser**: Chrome, Firefox, Safari, or Edge (any modern browser)

## Installation

### Step 1: Install Python

If you don't have Python installed:
1. Visit https://www.python.org/downloads/
2. Download Python 3.8 or higher for your operating system
3. Run the installer and **check "Add Python to PATH"**
4. Click "Install Now"

### Step 2: Navigate to Application Folder

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)
2. Navigate to the application directory:
```bash
cd "C:\Users\YourUsername\Documents\Financial analysis software\expense_tracker"
```

### Step 3: Run the Startup Script

**On Windows:**
```
Double-click: start.bat
```

**On macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

The script will:
- Create a virtual environment (first run only)
- Install all required dependencies
- Start the application

## Using the Application

### First Time Setup

1. The application automatically opens in your browser at `http://localhost:5000`
2. Default categories are created automatically (Groceries, Restaurants, etc.)

### Dashboard

- **View Summary**: Income, expenses, and net balance for the selected period
- **See Charts**: Visual breakdown of expenses by category
- **Recent Transactions**: Quick view of 5 most recent transactions
- **Change Period**: Select Daily, Weekly, Monthly, or Annual views

### Managing Transactions

1. Click **"Transactions"** in the sidebar
2. **Add Transaction**: Click "Add Transaction" button
   - Fill in Date, Description, Type (Income/Expense), Category, and Amount
   - Click "Save Transaction"
3. **Edit Transaction**: Click the edit icon in the table
4. **Delete Transaction**: Click the delete icon
5. **Toggle Exclude**: Click the eye-slash icon to exclude from reports
6. **Search**: Type in the search box to find transactions
7. **Filter**: Use filters for Type and Category

### Creating Budgets

1. Click **"Budgets"** in the sidebar
2. Click **"Create Budget"** button
3. Select a category and enter budget amount
4. Choose time period (Daily, Weekly, Monthly, Annual)
5. Optionally check "Budget for excluded expenses"
6. Click "Create Budget"

The Budgets page shows:
- Budget amount for each category
- Color-coded status (under/over budget)
- Quick edit and delete options

### Uploading Bank Statements

1. Click **"Upload"** in the sidebar
2. Drag and drop a CSV or Excel file, or click to browse
3. Review the preview (first 10 rows)
4. Click "Confirm Upload" to import

Supported Formats:
- **CSV** (.csv) - Comma-separated values
- **Excel** (.xlsx, .xls) - Microsoft Excel files

File Requirements:
- Must have columns for: Date, Description, Amount
- Date format: YYYY-MM-DD or MM/DD/YYYY
- Amount as positive numbers

### Viewing Reports

1. Click **"Reports"** in the sidebar
2. **Spending Trends**: 6-month chart of expense trends
3. **Budget vs Actual**: Compare budgeted amounts with actual spending
4. **Category Breakdown**: Detailed breakdown of expenses by category

## File Structure

```
expense_tracker/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   └── utils/           # Helper functions
│   ├── data/
│   │   ├── uploads/         # Uploaded files
│   │   └── expense_tracker.db  # Database
│   ├── run.py              # Start the application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── templates/
│   │   └── index.html       # Main UI
│   └── static/
│       ├── css/style.css    # Styling
│       └── js/app.js        # Frontend logic
├── start.bat               # Windows startup script
├── start.sh                # Mac/Linux startup script
└── README.md               # This file
```

## Troubleshooting

### Application won't start

**Error: "Python is not installed"**
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH"

**Error: "Port 5000 is already in use"**
- Another application is using port 5000
- Option 1: Close that application
- Option 2: Change port in `backend/run.py` (line with `port=5000`)

### Browser won't open

- Manually open: http://localhost:5000
- Try a different browser

### File upload not working

- Check file size (max 16MB)
- Verify file format (CSV or Excel)
- Ensure file has Date, Description, and Amount columns

### Database issues

- Delete `backend/data/expense_tracker.db` file
- Restart the application (it will recreate the database)

## Data Backup

### Backing Up Your Data

Your data is stored in `backend/data/expense_tracker.db`. To backup:

1. Open the `expense_tracker` folder
2. Navigate to `backend/data/`
3. Copy `expense_tracker.db` to a safe location

### Restoring from Backup

1. Stop the application
2. Replace `backend/data/expense_tracker.db` with your backup
3. Restart the application

## Tips & Best Practices

### Category Management
- Create custom categories for better tracking
- Use consistent category names (e.g., always "Restaurants", not "Restaurant")
- Review and recategorize imported transactions if needed

### Budget Management
- Set realistic budgets based on your spending patterns
- Review budgets monthly and adjust as needed
- Create budgets for both regular and excluded expenses

### File Imports
- Ensure bank statements are in CSV or Excel format
- Check date formats match YYYY-MM-DD or MM/DD/YYYY
- Start with a small file to test the format

### Data Accuracy
- Review all transactions after file import
- Update categories for better reports
- Exclude non-regular or one-time expenses

## Advanced Features

### Excluding Expenses

Exclude transactions from budget and report calculations:
1. Go to Transactions
2. Click the eye-slash icon on any transaction
3. The transaction is now marked "Excluded"

### Custom Reports

Combine features for custom analysis:
- Use period selector for specific timeframes
- Filter by category to focus on spending areas
- Compare budgets vs actuals for insight

### Data Export

To export transaction data:
1. Save the database file: `backend/data/expense_tracker.db`
2. Use any SQLite viewer to access the data
3. Export as CSV or Excel

## API Documentation

The application provides REST APIs. Base URL: `http://localhost:5000/api`

### Categories
- `GET /categories/` - List all categories
- `POST /categories/` - Create category
- `PUT /categories/<id>` - Update category
- `DELETE /categories/<id>` - Delete category

### Transactions
- `GET /transactions/` - List transactions
- `POST /transactions/` - Create transaction
- `PUT /transactions/<id>` - Update transaction
- `DELETE /transactions/<id>` - Delete transaction
- `PUT /transactions/exclude/<id>` - Toggle exclude status

### Budgets
- `GET /budgets/` - List budgets
- `POST /budgets/` - Create budget
- `PUT /budgets/<id>` - Update budget
- `DELETE /budgets/<id>` - Delete budget

### Reports
- `GET /reports/summary` - Financial summary
- `GET /reports/by-category` - Category breakdown
- `GET /reports/budget-analysis` - Budget vs actual
- `GET /reports/trending` - Spending trends

### Uploads
- `POST /uploads/upload` - Upload and import file
- `POST /uploads/preview` - Preview file before upload

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Keyboard Shortcuts

- `Ctrl+K` - Focus search (future feature)
- `Esc` - Close modals

## Common Questions

**Q: Is my data secure?**
A: Yes! All data is stored locally on your computer in a SQLite database. No data is sent to external servers.

**Q: Can I access this from multiple computers?**
A: Currently, data is local to each computer. You can manually backup and transfer the database file.

**Q: How do I add more categories?**
A: Click on Transactions, then use the category filter dropdown to add new ones, or edit them from the Categories API.

**Q: What happens if I delete a transaction?**
A: It's permanently removed from the database. Make sure to backup first if concerned.

**Q: Can I import multiple files?**
A: Yes! Upload as many files as needed. Duplicate transactions aren't automatically detected.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the file structure and ensure all files are present
3. Check that Python and all dependencies are installed correctly
4. Try restarting the application

## License

This software is provided as-is for personal use.

## Version

**Version**: 1.0.0
**Last Updated**: February 2026

---

Enjoy managing your finances with Expense Tracker! 💰
