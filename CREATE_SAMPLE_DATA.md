# How to Create Sample Data

## Overview

If you want to see how the application works without manually entering data, you can use the sample data script to populate the database with realistic transactions and budgets.

## Steps

### 1. Start the Application

First, make sure the application is running:
- **Windows**: Double-click `start.bat`
- **macOS/Linux**: Run `./start.sh`

Wait for it to fully start (you'll see the message about listening on port 5000).

### 2. Open a New Command Prompt/Terminal

**Windows:**
1. Open a new Command Prompt window (don't close the original)
2. Type: `cd C:\Users\YourUsername\Documents\Financial analysis software\expense_tracker\backend`
3. Skip to Step 4

**macOS/Linux:**
1. Open a new Terminal window
2. Type: `cd ~/Documents/Financial\ analysis\ software/expense_tracker/backend`
3. Skip to Step 4

### 3. Activate Virtual Environment

**Windows:**
```
venv\Scripts\activate
```

**macOS/Linux:**
```
source venv/bin/activate
```

### 4. Run the Sample Data Script

```
python create_sample_data.py
```

You should see:
```
Creating sample categories...
Creating sample transactions...
Creating sample budgets...
Sample data created successfully!

Summary:
  - Created XX categories
  - Created XXX transactions
  - Created XX budgets

You can now restart the application to see the sample data.
```

### 5. Refresh Your Browser

In your browser, press `F5` to refresh or go to `http://localhost:5000`

You should now see:
- Sample transactions in the Transactions tab
- Sample budgets in the Budgets tab
- Charts and data on the Dashboard

## What Data Is Created?

### Categories (17 total)
- **Expenses**: Groceries, Restaurants, Transportation, Utilities, Entertainment, Shopping, Healthcare, Insurance, Rent/Mortgage, Savings, Debt Payment
- **Income**: Salary, Freelance, Investment, Bonus

### Transactions (150+)
- 3 months of realistic transactions
- Mix of income and expenses
- Different amounts for each transaction
- Real merchant names

### Budgets (7 total)
- Monthly budgets for major expense categories
- Set at realistic amounts

## Important Notes

- ✅ Sample data is safe - it's stored in the same database as real data
- ✅ You can delete any sample transaction normally
- ✅ You can edit sample data to customize it
- ❌ Don't run the script twice - it will do nothing the second time

## Removing Sample Data

To delete all sample data:
1. Stop the application (Ctrl+C)
2. Delete the file: `backend/data/expense_tracker.db`
3. Restart the application
4. The database will be recreated empty

## Customizing Sample Data

You can edit `create_sample_data.py` to change:
- Sample transaction amounts
- Number of months of data
- Sample merchant names
- Budget amounts
- Categories

Then run it again (delete the database first to reset).
