# Makerspace User Data Analysis Scripts

This repository contains Python scripts for analyzing makerspace user data, including authorizations and access logs.

## Data Files

- `users.json` - User database containing account information, authorizations, and FOB codes
- `Space Access Reports.xlsx` - Monthly access logs with FOB entry timestamps

## Scripts

### 1. analyze_authorizations.py

Analyzes and reports on all distinct authorization types in the user database.

**Usage:**
```bash
python3 analyze_authorizations.py
```

**Output:**
- Console output showing:
  - Total number of users
  - Total distinct authorizations
  - Count of users with each authorization type (sorted by frequency)

**Example output:**
```
Authorization Analysis
============================================================
Total users: 624
Total distinct authorizations: 15

Authorization Counts (sorted by count, descending):
------------------------------------------------------------
 148  Woodshop Orientation
  96  Woodshop Power Tools
  95  Woodshop 101
...
```

### 2. metal_users.py

Extracts users who have metal shop authorizations (Metal Mill, Metal Lathe, or SouthBendLathe).

**Usage:**
```bash
python3 metal_users.py
```

**Output:**
- `metal_users.csv` - CSV file containing:
  - `full_name` - User's full name
  - `authorizations` - Comma-separated list of metal shop authorizations

### 3. users_with_authorizations.py

Generates a comprehensive list of all users who have any authorizations.

**Usage:**
```bash
python3 users_with_authorizations.py
```

**Output:**
- `users_with_authorizations.csv` - CSV file containing:
  - `account_id` - User's account ID
  - `full_name` - User's full name
  - `fob_code` - User's FOB code (first one if multiple exist)
  - `authorizations` - Comma-separated list of all authorizations

### 4. analyze_fob_access.py

Analyzes FOB access logs from the Excel file for recent months, aggregating access by user across all their FOB codes.

**Usage:**
```bash
python3 analyze_fob_access.py [--months N] [--top T]
```

**Options:**
- `--months N` - Number of past months to analyze (default: 3, includes current month + N past months)
- `--top T` - Number of top users to include in top_users.csv (default: 100)
- `-O`, `--only-one-fob` - Only include users with exactly one fob code in top_users.csv

**Examples:**
```bash
# Analyze last 4 months (current + 3 past), show top 100 users
python3 analyze_fob_access.py

# Analyze last 2 months (current + 1 past), show top 50 users
python3 analyze_fob_access.py --months 1 --top 50

# Analyze last 7 months (current + 6 past), show top 200 users
python3 analyze_fob_access.py --months 6 --top 200
```

**Output:**
- `fob_access_report.csv` - CSV file containing all users with access, sorted by access count (descending):
  - `account_id` - User's account ID
  - `first_name` - User's first name
  - `last_name` - User's last name
  - `preferred_name` - User's preferred name
  - `full_name` - User's full name
  - `access_count` - Total number of accesses across all user's FOBs (sorted descending)
  - `last_access_date` - Date of the most recent access (YYYY-MM-DD format)
- `top_users.csv` - CSV file containing top N users (configurable via --top) with highest access counts, sorted by last name, first name
- `print_top_user_labels.sh` - Auto-generated bash script to print labels for top users (for use with [pt-p710bt-label-maker](https://github.com/jantman/pt-p710bt-label-maker))
- Console output showing processing summary

**Notes:**
- Access is aggregated by user - if a user has multiple FOB codes, all their accesses are combined
- FOB codes are looked up from users.json
- Users without FOB codes in users.json will not appear in the report

### 5. combine_user_access.py

Combines user authorization data with FOB access statistics to create a comprehensive report.

**Usage:**
```bash
python3 combine_user_access.py
```

**Prerequisites:**
- `users_with_authorizations.csv` must exist (run `users_with_authorizations.py` first)
- `fob_access_report.csv` must exist (run `analyze_fob_access.py` first)

**Output:**
- `common_users.csv` - CSV file containing:
  - `account_id` - User's account ID
  - `full_name` - User's full name
  - `fob_code` - User's FOB code (10-digit zero-padded string)
  - `access_count` - Number of accesses in analyzed period (0 if no access)
  - `last_access_date` - Date of last access (empty if no access)
  - `authorizations` - Comma-separated list of all authorizations
- Console output showing summary statistics

**Note:** Users are sorted by access count (descending), then by full name.

## Important Notes

- **FOB Code Format**: All FOB codes are stored as 10-digit zero-padded strings (e.g., "0001234567") to ensure proper matching and Excel compatibility.
- The access analysis period is configurable in `analyze_fob_access.py` using the `--months` parameter.

## Requirements

- Python 3.x
- pandas
- python-dateutil
- openpyxl (for Excel file reading)

Install dependencies:
```bash
pip install pandas python-dateutil openpyxl
```
