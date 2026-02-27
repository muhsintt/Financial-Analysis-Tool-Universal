import pandas as pd
from datetime import datetime
import csv

def detect_transaction_type(description, amount):
    """Detect if transaction is income or expense"""
    if amount < 0:
        return 'expense'
    return 'income'

def categorize_transaction(description, category_id=None, user_id=None):
    """
    Automatically categorize transaction based on description using database rules.
    Falls back to rule-based matching if category_id not found.
    Returns category_id or None
    """
    from app.models.categorization_rule import CategorizationRule
    from app.models.category import Category
    
    # If category_id provided, validate it exists and belongs to user
    if category_id and user_id:
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if category:
            return category_id
    elif category_id and not user_id:
        # Fallback for cases where user_id is not provided
        category = Category.query.get(category_id)
        if category:
            return category_id
    
    # Check categorization rules in priority order (filter by user if provided)
    if user_id:
        rules = CategorizationRule.query.filter_by(
            is_active=True, 
            user_id=user_id
        ).order_by(CategorizationRule.priority.desc()).all()
    else:
        rules = CategorizationRule.query.filter_by(is_active=True).order_by(
            CategorizationRule.priority.desc()
        ).all()
    
    for rule in rules:
        if rule.matches(description):
            return rule.category_id
    
    # Fallback: Hardcoded rules if no database rules match
    description_lower = description.lower()
    
    # Try to find category by name
    category_map = {
        'Groceries': ['grocery', 'supermarket', 'food', 'market', 'frys', 'walmart', 'safeway', 'whole foods'],
        'Restaurants & Dining': ['restaurant', 'cafe', 'pizza', 'burger', 'coffee', 'mcd', 'chipotle', 'chick-fil'],
        'Transportation': ['uber', 'taxi', 'gas', 'fuel', 'parking', 'transit', 'amtrak', 'lyft', 'shell', 'chevron', 'speedway'],
        'Utilities': ['electric', 'water', 'gas bill', 'internet', 'phone', 'comcast', 'verizon', 'at&t', 'utility', 'city of'],
        'Entertainment/Subscriptions': ['movie', 'concert', 'game', 'entertainment', 'netflix', 'hulu', 'disney', 'steam', 'playstation', 'xbox', 'nintendo'],
        'Shopping/Retail': ['amazon', 'walmart', 'target', 'mall', 'store', 'shop', 'ebay', 'etsy', 'best buy'],
        'Health & Pharmacy': ['doctor', 'hospital', 'pharmacy', 'medicine', 'cvs', 'walgreens', 'dental', 'clinic', 'health'],
        'Insurance': ['insurance', 'aarp', 'geico', 'state farm'],
        'Housing': ['rent', 'mortgage', 'landlord', 'property'],
        'Income': ['salary', 'wages', 'paycheck', 'payroll'],
    }
    
    for category_name, keywords in category_map.items():
        if any(word in description_lower for word in keywords):
            if user_id:
                category = Category.query.filter_by(name=category_name, user_id=user_id).first()
            else:
                category = Category.query.filter_by(name=category_name).first()
            if category:
                return category.id
    
    # Default to 'Uncategorized'
    if user_id:
        default_category = Category.query.filter_by(name='Uncategorized', user_id=user_id).first()
    else:
        default_category = Category.query.filter_by(name='Uncategorized').first()
    return default_category.id if default_category else None


def _parse_date(date_str):
    """Try multiple date formats and return a date object, or None."""
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except:
            pass
    return None


def process_csv_file(filepath, limit=None, user_id=None, column_mapping=None):
    """Process CSV file and extract transactions.

    column_mapping (optional) is a dict with keys:
        date_col, description_col, amount_col, category_col (optional)
    When provided, those exact column names are used and all other columns
    are collected into the transaction notes.
    """
    transactions = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break

                if column_mapping:
                    date_str   = row.get(column_mapping['date_col'], '')
                    desc       = row.get(column_mapping['description_col'], '')
                    amount_str = row.get(column_mapping['amount_col'], '')
                    cat_str    = row.get(column_mapping.get('category_col', ''), '') if column_mapping.get('category_col') else ''
                    # Collect extra columns into notes
                    known = {column_mapping['date_col'], column_mapping['description_col'], column_mapping['amount_col']}
                    if column_mapping.get('category_col'):
                        known.add(column_mapping['category_col'])
                    notes = ' | '.join(f"{k}: {v}" for k, v in row.items() if k not in known and str(v).strip())
                else:
                    date_str   = (row.get('Date') or row.get('date') or row.get('Transaction Date')
                                  or row.get('Post Date') or row.get('Posted Date') or '')
                    desc       = (row.get('Description') or row.get('description')
                                  or row.get('Memo') or row.get('Payee') or row.get('payee') or '')
                    amount_str = (row.get('Amount') or row.get('amount')
                                  or row.get('Debit') or '')
                    cat_str    = row.get('Category') or row.get('category') or ''
                    notes      = ''

                if not all([date_str, desc, amount_str]):
                    continue

                transaction_date = _parse_date(str(date_str))
                if transaction_date is None:
                    continue

                try:
                    amount = float(str(amount_str).replace('$', '').replace(',', ''))
                except (ValueError, TypeError):
                    continue

                trans_type = detect_transaction_type(desc, amount)
                amount = abs(amount)

                # Category: honour CSV value from template if present, else auto-detect
                category_id = None
                if cat_str and column_mapping:
                    from app.models.category import Category
                    cat = Category.query.filter_by(name=cat_str.strip(), user_id=user_id).first()
                    if not cat:
                        cat = Category.query.filter(Category.name.ilike(cat_str.strip())).first()
                    if cat:
                        category_id = cat.id
                if not category_id:
                    category_id = categorize_transaction(desc, user_id=user_id)

                transactions.append({
                    'date': transaction_date,
                    'description': desc.strip(),
                    'amount': amount,
                    'type': trans_type,
                    'category_id': category_id,
                    'notes': notes,
                })

        return transactions

    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")

def process_excel_file(filepath, limit=None, user_id=None, column_mapping=None):
    """Process Excel file and extract transactions.

    column_mapping (optional) has the same shape as for process_csv_file.
    """
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

            cat_val = None
            notes_str = ''

            if column_mapping:
                date_val   = row.get(column_mapping['date_col'])
                desc_val   = row.get(column_mapping['description_col'])
                amount_val = row.get(column_mapping['amount_col'])
                if column_mapping.get('category_col'):
                    cat_val = row.get(column_mapping['category_col'])
                known = {column_mapping['date_col'], column_mapping['description_col'], column_mapping['amount_col']}
                if column_mapping.get('category_col'):
                    known.add(column_mapping['category_col'])
                notes_str = ' | '.join(
                    f"{k}: {v}" for k, v in row.items()
                    if k not in known and not pd.isna(v) and str(v).strip()
                )
            else:
                # Try exact matches first
                if 'posted date' in column_map:
                    date_val = row[column_map['posted date']]
                elif 'post date' in column_map:
                    date_val = row[column_map['post date']]
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

            # Category from template column if present, else auto-detect
            category_id = None
            if cat_val is not None and not pd.isna(cat_val) and str(cat_val).strip():
                from app.models.category import Category
                cat = Category.query.filter_by(name=str(cat_val).strip(), user_id=user_id).first()
                if not cat:
                    cat = Category.query.filter(Category.name.ilike(str(cat_val).strip())).first()
                if cat:
                    category_id = cat.id
            if not category_id:
                category_id = categorize_transaction(str(desc_val), user_id=user_id)

            transactions.append({
                'date': transaction_date,
                'description': str(desc_val).strip(),
                'amount': amount,
                'type': trans_type,
                'category_id': category_id,
                'notes': notes_str,
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

