import pandas as pd
from datetime import datetime
import csv
import io
import re

def detect_transaction_type(description, amount, type_hint=None):
    """Detect if transaction is income or expense.
    
    type_hint can be 'credit'/'debit' from a bank statement column.
    """
    if type_hint:
        hint_lower = str(type_hint).strip().lower()
        if hint_lower in ('credit', 'cr', 'deposit', 'credits'):
            return 'income'
        elif hint_lower in ('debit', 'dr', 'withdrawal', 'debits'):
            return 'expense'
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
    
    # Check categorization rules in priority order.
    # Personal rules (user_id=user_id) take precedence over system rules (user_id=None).
    if user_id:
        personal_rules = CategorizationRule.query.filter_by(
            is_active=True,
            user_id=user_id
        ).order_by(CategorizationRule.priority.desc()).all()
        system_rules = CategorizationRule.query.filter(
            CategorizationRule.is_active == True,
            CategorizationRule.user_id.is_(None)
        ).order_by(CategorizationRule.priority.desc()).all()
        rules = personal_rules + system_rules
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
                # Try user-specific category first, then fall back to system category
                category = Category.query.filter_by(name=category_name, user_id=user_id).first()
                if not category:
                    category = Category.query.filter_by(name=category_name, user_id=None).first()
            else:
                category = Category.query.filter_by(name=category_name).first()
            if category:
                return category.id

    # Default to 'Uncategorized'
    if user_id:
        default_category = Category.query.filter_by(name='Uncategorized', user_id=user_id).first()
        if not default_category:
            default_category = Category.query.filter_by(name='Uncategorized', user_id=None).first()
    else:
        default_category = Category.query.filter_by(name='Uncategorized').first()
    return default_category.id if default_category else None


def _parse_date(date_str):
    """Try multiple date formats and return a date object, or None."""
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except:
            pass
    return None


def _repair_csv_lines(filepath):
    """Pre-process CSV to fix unquoted numbers containing commas (e.g. 1,800.41).
    
    Strategy: If a row has MORE fields than the header, rejoin numeric fragments.
    If a row has the CORRECT number of fields but an amount field looks like it was
    split (pure integer in amount position, decimal fragment in next position, and
    the last expected field is missing/empty), attempt repair by shifting.
    Returns a list of repaired lines (strings) suitable for csv.DictReader.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    
    if not raw_lines:
        return raw_lines
    
    # Count expected fields from header
    header_row = next(csv.reader([raw_lines[0]]))
    header_fields = len(header_row)
    
    # Identify likely amount column index (for same-field-count repair)
    amount_idx = None
    for idx, h in enumerate(header_row):
        hl = h.strip().lower()
        if hl in ('amount', 'transaction amount', 'debit', 'credit'):
            amount_idx = idx
            break
    
    repaired = [raw_lines[0]]
    for line in raw_lines[1:]:
        fields = next(csv.reader([line]))
        
        if len(fields) > header_fields:
            # Row has too many fields — rejoin numeric fragments
            new_fields = []
            i = 0
            while i < len(fields):
                if (i + 1 < len(fields) and
                    re.match(r'^\d+$', fields[i].strip()) and
                    re.match(r'^\d+(\.\d+)?$', fields[i+1].strip())):
                    joined = fields[i].strip() + fields[i+1].strip()
                    new_fields.append(joined)
                    i += 2
                else:
                    new_fields.append(fields[i])
                    i += 1
                if len(new_fields) + (len(fields) - i) == header_fields:
                    new_fields.extend(fields[i:])
                    break
            if len(new_fields) == header_fields:
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(new_fields)
                repaired.append(output.getvalue())
            else:
                repaired.append(line)
        elif len(fields) == header_fields and amount_idx is not None:
            # Check if amount field looks like a split number:
            # Only trigger if the raw line has more commas than expected for unquoted fields,
            # indicating a number like "1,800.41" was split.
            # Count unquoted commas in raw line
            raw_field_count = len(next(csv.reader([line.strip()])))
            # Also check: amt is pure integer AND next is decimal fragment
            amt_val = fields[amount_idx].strip() if amount_idx < len(fields) else ''
            next_val = fields[amount_idx + 1].strip() if amount_idx + 1 < len(fields) else ''
            
            # Only repair if the pattern strongly suggests a split number
            # Use strict thousands pattern: 1-2 digit prefix + exactly 3-digit group + optional decimal
            if (re.match(r'^\d{1,2}$', amt_val) and
                re.match(r'^\d{3}\.\d{1,2}$', next_val)):
                # Pattern like "1" + "800.41" strongly suggests "1,800.41" was split
                joined_amount = amt_val + next_val
                new_fields = fields[:amount_idx] + [joined_amount] + fields[amount_idx+2:]
                if len(new_fields) == header_fields - 1:
                    new_fields.append('')
                if len(new_fields) == header_fields:
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(new_fields)
                    repaired.append(output.getvalue())
                else:
                    repaired.append(line)
            else:
                repaired.append(line)
        else:
            repaired.append(line)
    
    return repaired


def process_csv_file(filepath, limit=None, user_id=None, column_mapping=None):
    """Process CSV file and extract transactions.

    column_mapping (optional) is a dict with keys:
        date_col, description_col, amount_col, category_col (optional)
    When provided, those exact column names are used and all other columns
    are collected into the transaction notes.
    """
    transactions = []

    try:
        # Repair CSV lines with unquoted numeric commas
        repaired_lines = _repair_csv_lines(filepath)
        reader = csv.DictReader(io.StringIO(''.join(repaired_lines)))

        for i, row in enumerate(reader):
            if limit and i >= limit:
                break

            if column_mapping:
                date_str   = row.get(column_mapping['date_col'], '')
                desc       = row.get(column_mapping['description_col'], '')
                cat_str    = row.get(column_mapping.get('category_col', ''), '') if column_mapping.get('category_col') else ''

                # Handle amount: either single amount_col or separate debit/credit columns
                amount_str = ''
                type_hint = None
                debit_col = column_mapping.get('debit_col')
                credit_col = column_mapping.get('credit_col')

                if debit_col or credit_col:
                    # Separate debit/credit columns
                    debit_val = row.get(debit_col, '').strip() if debit_col else ''
                    credit_val = row.get(credit_col, '').strip() if credit_col else ''
                    # Clean currency symbols
                    debit_clean = debit_val.replace('$', '').replace(',', '').strip() if debit_val else ''
                    credit_clean = credit_val.replace('$', '').replace(',', '').strip() if credit_val else ''

                    try:
                        debit_num = float(debit_clean) if debit_clean and debit_clean != '0' else 0
                    except (ValueError, TypeError):
                        debit_num = 0
                    try:
                        credit_num = float(credit_clean) if credit_clean and credit_clean != '0' else 0
                    except (ValueError, TypeError):
                        credit_num = 0

                    if credit_num > 0:
                        amount_str = str(credit_num)
                        type_hint = 'credit'
                    elif debit_num > 0:
                        amount_str = str(debit_num)
                        type_hint = 'debit'
                    elif debit_num < 0:
                        # Negative in debit column means credit
                        amount_str = str(abs(debit_num))
                        type_hint = 'credit'
                    else:
                        continue  # No amount found
                else:
                    amount_str = row.get(column_mapping.get('amount_col', ''), '')

                # Collect extra columns into notes
                known = {column_mapping['date_col'], column_mapping['description_col']}
                if column_mapping.get('amount_col'):
                    known.add(column_mapping['amount_col'])
                if column_mapping.get('category_col'):
                    known.add(column_mapping['category_col'])
                if debit_col:
                    known.add(debit_col)
                if credit_col:
                    known.add(credit_col)
                notes = ' | '.join(f"{k}: {v}" for k, v in row.items() if k not in known and str(v).strip())
            else:
                date_str   = (row.get('Date') or row.get('date') or row.get('Transaction Date')
                              or row.get('Post Date') or row.get('Posted Date') or '')
                desc       = (row.get('Description') or row.get('description')
                              or row.get('Transaction Description') or row.get('transaction description')
                              or row.get('Memo') or row.get('Payee') or row.get('payee') or '')
                cat_str    = row.get('Category') or row.get('category') or ''
                notes      = ''
                type_hint  = None

                # Check for separate Debit/Credit columns
                debit_val = (row.get('Debit') or row.get('debit') or row.get('Withdrawals') or '').strip()
                credit_val = (row.get('Credit') or row.get('credit') or row.get('Deposits') or '').strip()

                if debit_val or credit_val:
                    debit_clean = debit_val.replace('$', '').replace(',', '') if debit_val else ''
                    credit_clean = credit_val.replace('$', '').replace(',', '') if credit_val else ''
                    try:
                        debit_num = float(debit_clean) if debit_clean else 0
                    except (ValueError, TypeError):
                        debit_num = 0
                    try:
                        credit_num = float(credit_clean) if credit_clean else 0
                    except (ValueError, TypeError):
                        credit_num = 0

                    if credit_num > 0:
                        amount_str = str(credit_num)
                        type_hint = 'credit'
                    elif debit_num > 0:
                        amount_str = str(debit_num)
                        type_hint = 'debit'
                    else:
                        amount_str = (row.get('Amount') or row.get('amount')
                                     or row.get('Transaction Amount') or row.get('transaction amount') or '')
                else:
                    amount_str = (row.get('Amount') or row.get('amount')
                                  or row.get('Transaction Amount') or row.get('transaction amount') or '')

                # Check for a Type/Transaction Type column with text values
                if not type_hint:
                    type_col_val = (row.get('Type') or row.get('type') or
                                   row.get('Transaction Type') or row.get('Trans Type') or '')
                    if type_col_val:
                        type_hint = type_col_val

            if not all([date_str, desc, amount_str]):
                continue

            transaction_date = _parse_date(str(date_str))
            if transaction_date is None:
                continue

            try:
                amount = float(str(amount_str).replace('$', '').replace(',', ''))
            except (ValueError, TypeError):
                continue

            trans_type = detect_transaction_type(desc, amount, type_hint)
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
            type_hint = None

            if column_mapping:
                date_val   = row.get(column_mapping['date_col'])
                desc_val   = row.get(column_mapping['description_col'])
                if column_mapping.get('category_col'):
                    cat_val = row.get(column_mapping['category_col'])

                # Handle amount: single column or separate debit/credit
                debit_col = column_mapping.get('debit_col')
                credit_col = column_mapping.get('credit_col')

                if debit_col or credit_col:
                    debit_raw = row.get(debit_col) if debit_col else None
                    credit_raw = row.get(credit_col) if credit_col else None

                    debit_num = 0
                    credit_num = 0
                    if debit_raw is not None and not pd.isna(debit_raw):
                        try:
                            debit_num = float(str(debit_raw).replace('$', '').replace(',', ''))
                        except (ValueError, TypeError):
                            debit_num = 0
                    if credit_raw is not None and not pd.isna(credit_raw):
                        try:
                            credit_num = float(str(credit_raw).replace('$', '').replace(',', ''))
                        except (ValueError, TypeError):
                            credit_num = 0

                    if credit_num > 0:
                        amount_val = credit_num
                        type_hint = 'credit'
                    elif debit_num > 0:
                        amount_val = debit_num
                        type_hint = 'debit'
                    elif debit_num < 0:
                        amount_val = abs(debit_num)
                        type_hint = 'credit'
                    else:
                        amount_val = None
                else:
                    amount_val = row.get(column_mapping.get('amount_col'))

                known = {column_mapping['date_col'], column_mapping['description_col']}
                if column_mapping.get('amount_col'):
                    known.add(column_mapping['amount_col'])
                if column_mapping.get('category_col'):
                    known.add(column_mapping['category_col'])
                if debit_col:
                    known.add(debit_col)
                if credit_col:
                    known.add(credit_col)
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

                # Amount: check separate debit/credit columns first
                if 'debit' in column_map and 'credit' in column_map:
                    debit_raw = row[column_map['debit']]
                    credit_raw = row[column_map['credit']]
                    debit_num = 0
                    credit_num = 0
                    if not pd.isna(debit_raw):
                        try:
                            debit_num = float(str(debit_raw).replace('$', '').replace(',', ''))
                        except (ValueError, TypeError):
                            debit_num = 0
                    if not pd.isna(credit_raw):
                        try:
                            credit_num = float(str(credit_raw).replace('$', '').replace(',', ''))
                        except (ValueError, TypeError):
                            credit_num = 0

                    if credit_num > 0:
                        amount_val = credit_num
                        type_hint = 'credit'
                    elif debit_num > 0:
                        amount_val = debit_num
                        type_hint = 'debit'
                    else:
                        amount_val = None
                elif 'amount' in column_map:
                    amount_val = row[column_map['amount']]
                elif 'debit' in column_map:
                    amount_val = row[column_map['debit']]
                    type_hint = 'debit'
                elif 'credit' in column_map:
                    amount_val = row[column_map['credit']]
                    type_hint = 'credit'

                # Check for Type column
                if not type_hint:
                    for tc in ['type', 'transaction type', 'trans type']:
                        if tc in column_map:
                            tv = row[column_map[tc]]
                            if not pd.isna(tv):
                                type_hint = str(tv)
                            break
            
            # Skip if missing required fields or if they are NaN
            if date_val is None or desc_val is None or amount_val is None:
                continue
            
            # Skip NaN values
            if pd.isna(date_val) or pd.isna(desc_val) or (isinstance(amount_val, float) and pd.isna(amount_val)):
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
            
            trans_type = detect_transaction_type(str(desc_val), amount, type_hint)
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

