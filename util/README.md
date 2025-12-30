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

Analyzes FOB access logs from the Excel file for recent months.

**Usage:**
```bash
python3 analyze_fob_access.py [--months N]
```

**Options:**
- `--months N` - Number of past months to analyze (default: 3, includes current month + N past months)

**Examples:**
```bash
# Analyze last 4 months (current + 3 past)
python3 analyze_fob_access.py

# Analyze last 2 months (current + 1 past)
python3 analyze_fob_access.py --months 1

# Analyze last 7 months (current + 6 past)
python3 analyze_fob_access.py --months 6
```

**Output:**
- `fob_access_report.csv` - CSV file containing:
  - `fob_code` - FOB code used for access (10-digit zero-padded string)
  - `access_count` - Number of times this FOB was used (sorted descending)
  - `last_access_date` - Date of the most recent access (YYYY-MM-DD format)
- Console output showing processing summary

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
