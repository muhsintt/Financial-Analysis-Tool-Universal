import pandas as pd
from datetime import datetime
import csv

def detect_transaction_type(description, amount):
    """Detect if transaction is income or expense"""
    if amount < 0:
        return 'expense'
    return 'income'

def categorize_transaction(description):
    """Automatically categorize transaction based on description"""
    description_lower = description.lower()
    
    # Expense categories
    if any(word in description_lower for word in ['grocery', 'supermarket', 'food', 'market', 'frys', 'walmart', 'safeway', 'whole foods']):
        return 'Groceries'
    elif any(word in description_lower for word in ['restaurant', 'cafe', 'pizza', 'burger', 'coffee', 'mcd', 'chipotle', 'chick-fil']):
        return 'Restaurants'
    elif any(word in description_lower for word in ['uber', 'taxi', 'gas', 'fuel', 'parking', 'transit', 'amtrak', 'lyft', 'shell', 'chevron', 'speedway']):
        return 'Transportation'
    elif any(word in description_lower for word in ['electric', 'water', 'gas bill', 'internet', 'phone', 'comcast', 'verizon', 'at&t', 'utility', 'city of']):
        return 'Utilities'
    elif any(word in description_lower for word in ['movie', 'concert', 'game', 'entertainment', 'netflix', 'hulu', 'disney', 'steam', 'playstation', 'xbox', 'nintendo']):
        return 'Entertainment'
    elif any(word in description_lower for word in ['amazon', 'walmart', 'target', 'mall', 'store', 'shop', 'ebay', 'etsy', 'best buy']):
        return 'Shopping'
    elif any(word in description_lower for word in ['doctor', 'hospital', 'pharmacy', 'medicine', 'cvs', 'walgreens', 'dental', 'clinic', 'health']):
        return 'Healthcare'
    elif any(word in description_lower for word in ['insurance', 'aarp', 'geico', 'state farm']):
        return 'Insurance'
    elif any(word in description_lower for word in ['rent', 'mortgage', 'landlord', 'property']):
        return 'Rent/Mortgage'
    elif any(word in description_lower for word in ['salary', 'wages', 'paycheck', 'payroll']):
        return 'Salary'
    elif any(word in description_lower for word in ['investment', 'dividend', 'interest', 'stock', 'broker']):
        return 'Investment'
    elif any(word in description_lower for word in ['paypal', 'stripe', 'square']):
        return 'Online Payment'
    elif any(word in description_lower for word in ['atm', 'withdrawal', 'cash']):
        return 'Cash'
    
    # Default
    return 'Other'

def process_csv_file(filepath, limit=None):
    """Process CSV file and extract transactions"""
    transactions = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                
                # Try to detect date, description, and amount columns
                date_str = row.get('Date') or row.get('date') or row.get('Transaction Date')
                desc = row.get('Description') or row.get('description') or row.get('Memo')
                amount_str = row.get('Amount') or row.get('amount') or row.get('Debit')
                
                if not all([date_str, desc, amount_str]):
                    continue
                
                try:
                    # Parse date
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    try:
                        transaction_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                    except:
                        continue
                
                # Parse amount
                amount = float(amount_str.replace('$', '').replace(',', ''))
                
                trans_type = detect_transaction_type(desc, amount)
                amount = abs(amount)  # Store as positive
                
                transactions.append({
                    'date': transaction_date,
                    'description': desc.strip(),
                    'amount': amount,
                    'type': trans_type,
                    'category': categorize_transaction(desc)
                })
        
        return transactions
    
    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")

def process_excel_file(filepath, limit=None):
    """Process Excel file and extract transactions"""
    transactions = []
    
    try:
        df = pd.read_excel(filepath)
        
        for i, row in df.iterrows():
            if limit and i >= limit:
                break
            
            # Initialize values
            date_val = None
            desc_val = None
            amount_val = None
            
            # Map columns with exact name matching (highest priority)
            column_map = {col.lower(): col for col in df.columns}
            
            # Try exact matches first
            if 'posted date' in column_map:
                date_val = row[column_map['posted date']]
            elif 'date' in column_map:
                date_val = row[column_map['date']]
            elif 'transaction date' in column_map:
                date_val = row[column_map['transaction date']]
            
            # Payee is the best description match
            if 'payee' in column_map:
                desc_val = row[column_map['payee']]
            elif 'description' in column_map:
                desc_val = row[column_map['description']]
            elif 'memo' in column_map:
                desc_val = row[column_map['memo']]
            
            # Amount
            if 'amount' in column_map:
                amount_val = row[column_map['amount']]
            elif 'debit' in column_map:
                amount_val = row[column_map['debit']]
            elif 'credit' in column_map:
                amount_val = row[column_map['credit']]
            
            # Skip if missing required fields or if they are NaN
            if date_val is None or desc_val is None or amount_val is None:
                continue
            
            # Skip NaN values
            if pd.isna(date_val) or pd.isna(desc_val) or pd.isna(amount_val):
                continue
            
            try:
                # Parse date
                if isinstance(date_val, str):
                    try:
                        transaction_date = datetime.strptime(date_val, '%Y-%m-%d').date()
                    except:
                        try:
                            transaction_date = datetime.strptime(date_val, '%m/%d/%Y').date()
                        except:
                            continue
                else:
                    transaction_date = pd.to_datetime(date_val).date()
            except:
                continue
            
            # Parse amount - handle NaN and convert to float
            try:
                if isinstance(amount_val, str):
                    amount = float(amount_val.replace('$', '').replace(',', ''))
                else:
                    amount = float(amount_val)
            except (ValueError, TypeError):
                continue
            
            # Skip zero amounts
            if amount == 0:
                continue
            
            trans_type = detect_transaction_type(str(desc_val), amount)
            amount = abs(amount)
            
            transactions.append({
                'date': transaction_date,
                'description': str(desc_val).strip(),
                'amount': amount,
                'type': trans_type,
                'category': categorize_transaction(str(desc_val))
            })
        
        return transactions
    
    except Exception as e:
        raise Exception(f"Error processing Excel: {str(e)}")

def process_delete_file(file):
    """
    Process a file containing transactions to delete.
    Supports two formats:
    1. ID-based: CSV/Excel with 'id', 'transaction_id', 'ID', or 'Transaction ID' column
    2. Bank statement format: Matches by description/payee and amount (e.g., 2025_JAN_FIN.xlsx)
    
    For bank statement format, looks for columns: Payee/Description, Amount/Transaction Amount
    """
    from app.models.transaction import Transaction
    
    try:
        transaction_ids = []
        filename = file.filename.lower()
        
        if filename.endswith('.csv'):
            # Process CSV
            df = pd.read_csv(file)
        elif filename.endswith(('.xlsx', '.xls')):
            # Process Excel
            df = pd.read_excel(file)
        else:
            raise ValueError("File must be CSV or Excel format")
        
        # Try ID-based deletion first
        id_column = None
        for col_name in ['id', 'transaction_id', 'ID', 'Transaction ID']:
            if col_name in df.columns:
                id_column = col_name
                break
        
        # If ID column found, use that
        if id_column is not None:
            for idx, val in df[id_column].items():
                try:
                    if pd.notna(val):
                        transaction_ids.append(int(val))
                except (ValueError, TypeError):
                    continue
            
            if transaction_ids:
                return transaction_ids
        
        # Otherwise, try bank statement format matching
        payee_column = None
        amount_column = None
        
        # Find payee/description column
        for col_name in ['Payee', 'Description', 'payee', 'description', 'PAYEE', 'DESCRIPTION', 'Merchant', 'merchant']:
            if col_name in df.columns:
                payee_column = col_name
                break
        
        # Find amount column
        for col_name in ['Amount', 'amount', 'Transaction Amount', 'transaction amount', 'AMOUNT', 'Value', 'value']:
            if col_name in df.columns:
                amount_column = col_name
                break
        
        # If we have both payee and amount columns, try to match transactions
        if payee_column and amount_column:
            for idx, row in df.iterrows():
                try:
                    payee = str(row[payee_column]).strip()
                    amount_str = str(row[amount_column]).strip()
                    
                    # Handle negative amounts (expenses)
                    amount = float(amount_str.replace('$', '').replace(',', ''))
                    amount = abs(amount)  # Always use absolute value for matching
                    
                    if pd.notna(payee) and payee and amount > 0:
                        # Find matching transaction
                        matching_trans = Transaction.query.filter(
                            Transaction.description.ilike(f'%{payee}%'),
                            Transaction.amount == amount
                        ).first()
                        
                        if matching_trans:
                            transaction_ids.append(matching_trans.id)
                
                except (ValueError, TypeError, AttributeError):
                    continue
            
            if transaction_ids:
                return transaction_ids
        
        # If we only have amount column, try matching by amount alone
        if amount_column and not transaction_ids:
            for idx, row in df.iterrows():
                try:
                    amount_str = str(row[amount_column]).strip()
                    amount = float(amount_str.replace('$', '').replace(',', ''))
                    amount = abs(amount)
                    
                    if amount > 0:
                        matching_trans = Transaction.query.filter(
                            Transaction.amount == amount
                        ).first()
                        
                        if matching_trans:
                            transaction_ids.append(matching_trans.id)
                
                except (ValueError, TypeError):
                    continue
            
            if transaction_ids:
                return transaction_ids
        
        if not transaction_ids:
            raise ValueError("No valid transaction IDs or matching transactions found in file. "
                           "File should contain 'ID' column or 'Payee' + 'Amount' columns for bank statement format.")
        
        return transaction_ids
    
    except Exception as e:
        raise Exception(f"Error processing delete file: {str(e)}")

