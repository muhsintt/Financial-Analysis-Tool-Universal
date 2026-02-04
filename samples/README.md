# Sample Categorization Rules

This directory contains sample categorization rule files in three formats:

## Files

| File | Format | Description |
|------|--------|-------------|
| `categorization_rules_sample.json` | JSON | JavaScript Object Notation format |
| `categorization_rules_sample.yaml` | YAML | YAML Ain't Markup Language format |
| `categorization_rules_sample.csv` | CSV | Comma-Separated Values format |

## Format Details

### JSON Format
```json
{
  "rules": [
    {
      "name": "Rule Name",
      "keywords": "keyword1,keyword2,keyword3",
      "category_name": "Category Name",
      "category_type": "expense|income",
      "priority": 10,
      "is_active": true
    }
  ]
}
```

### YAML Format
```yaml
rules:
  - name: Rule Name
    keywords: "keyword1,keyword2,keyword3"
    category_name: Category Name
    category_type: expense
    priority: 10
    is_active: true
```

### CSV Format
```csv
name,keywords,category_name,category_type,priority,is_active
Rule Name,"keyword1,keyword2,keyword3",Category Name,expense,10,true
```

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique name for the rule |
| `keywords` | Yes | Comma-separated list of keywords to match (case-insensitive) |
| `category_name` | Yes | Name of the category to assign |
| `category_type` | Recommended | Type of category: "expense" or "income" (used if category doesn't exist) |
| `priority` | No | Higher priority rules are checked first (default: 0) |
| `is_active` | No | Whether the rule is active (default: true) |

## Usage

1. Go to **Settings > Categorization Rules**
2. Click **Import Rules**
3. Select one of the sample files (JSON, YAML, or CSV)
4. Confirm the import

## Notes

- Keywords are matched case-insensitively against transaction descriptions
- If a category doesn't exist, it will be created automatically (if `category_type` is provided)
- Duplicate rule names are skipped during import
- Rules are applied based on priority (highest first)

## Sample Rules Included

1. **Grocery Stores** - Matches common grocery chains
2. **Restaurants & Dining** - Matches restaurants and cafes
3. **Gas Stations** - Matches fuel purchases
4. **Streaming Services** - Matches entertainment subscriptions
5. **Utilities** - Matches utility bills
6. **Payroll Income** - Matches salary deposits
7. **Bank Interest** - Matches interest and dividend income
8. **Bahá'í Fund Contributions** - Matches Bahá'í fund donations
