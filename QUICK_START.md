# QUICK START GUIDE - Expense Tracker

## Installation (2 Minutes)

### Windows Users
1. Open the `expense_tracker` folder
2. **Double-click `start.bat`**
3. Wait for the browser to open automatically
4. You're done! Start using the app

### macOS/Linux Users
1. Open Terminal
2. Navigate to the folder:
   ```
   cd ~/Documents/Financial\ analysis\ software/expense_tracker
   ```
3. Run:
   ```
   chmod +x start.sh
   ./start.sh
   ```
4. Open browser to http://localhost:5000

---

## First Things To Do

### 1. Add Your First Transaction
- Click "Transactions" in the sidebar
- Click "Add Transaction"
- Fill in the details and click "Save"

### 2. Create a Budget
- Click "Budgets" in the sidebar
- Click "Create Budget"
- Select category and amount
- Click "Create Budget"

### 3. Upload Bank Statement (Optional)
- Click "Upload" in the sidebar
- Drag and drop a CSV or Excel file
- Review the preview and confirm

### 4. View Your Dashboard
- Click "Dashboard" to see overview
- Check charts for spending breakdown
- See recent transactions

---

## Common Tasks

### Adding a Transaction
1. Transactions → Add Transaction
2. Fill: Date, Description, Type, Category, Amount
3. Save

### Editing a Transaction
1. Transactions → Click pencil icon
2. Make changes
3. Save

### Deleting a Transaction
1. Transactions → Click trash icon
2. Confirm deletion

### Excluding an Expense
1. Transactions → Click eye-slash icon
2. Transaction is now excluded from reports

### Viewing Reports
1. Click "Reports" in sidebar
2. See trends, budgets, and categories

---

## File Upload Tips

### Supported Files
- CSV (.csv)
- Excel (.xlsx, .xls)

### File Format Requirements
Your file should have columns for:
- Date (YYYY-MM-DD or MM/DD/YYYY)
- Description
- Amount (positive numbers)

### Example CSV
```
Date,Description,Amount
2024-02-01,Grocery Store,50.00
2024-02-02,Coffee Shop,5.50
2024-02-03,Gas Station,45.00
```

---

## Need Help?

### Application won't open?
- Make sure Python 3.8+ is installed
- Try opening http://localhost:5000 in your browser manually

### Port already in use?
- Another app is using port 5000
- Stop that app or restart your computer

### Data lost?
- Check `backend/data/expense_tracker.db` file exists
- If missing, you can restore from backup

### Still stuck?
- Read the full README.md file in this folder
- Check that all files exist in the folder structure

---

## Keyboard Shortcuts

- Press `Esc` to close any modal/dialog
- Click on column headers (future feature for sorting)

---

## Data Safety

✅ Your data is stored locally on your computer
✅ No data is sent to any server
✅ Backup: Copy `backend/data/expense_tracker.db` file

---

**Happy Budgeting! 💰**
