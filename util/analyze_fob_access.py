#!/usr/bin/env python3
"""
Analyze FOB code access from Space Access Reports.xlsx
Aggregates access by user (across all their FOBs) from users.json,
sorted by number of appearances.
"""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta


def main():
    parser = argparse.ArgumentParser(
        description="Analyze FOB access from Space Access Reports by user"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of past months to analyze (default: 3, meaning current month + 3 past months)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="Number of top users to include in top_users.csv (default: 100)",
    )
    parser.add_argument(
        "-O",
        "--only-one-fob",
        action="store_true",
        help="Only include users with exactly one fob code in top_users.csv",
    )
    args = parser.parse_args()

    # Load users.json to map fob codes to users
    print("Loading users.json...")
    with open("users.json") as f:
        users_data = json.load(f)

    # Create mapping of fob_code -> user
    fob_to_user = {}
    users_by_account_id = {}

    for user in users_data:
        account_id = user.get("account_id", "")
        users_by_account_id[account_id] = user

        # Map each fob code to this user
        for fob_code in user.get("fob_codes", []):
            fob_to_user[fob_code] = account_id

    print(f"Loaded {len(users_data)} users with {len(fob_to_user)} total FOB codes")
    print()

    # Read the Excel file
    excel_file = "Space Access Reports.xlsx"

    # Get current date and calculate target months
    today = datetime.now()

    # Generate list of target months (current month + N past months)
    target_months = []
    for i in range(args.months + 1):  # +1 to include current month
        month_date = today - relativedelta(months=i)
        target_months.append(month_date.strftime("%b %Y"))  # e.g., "Dec 2025"

    print(f"Analyzing FOB access for the following months: {', '.join(target_months)}")
    print("=" * 60)

    # Read all sheet names and find matching Log sheets
    xls = pd.ExcelFile(excel_file)
    log_sheets = []
    for sheet_name in xls.sheet_names:
        # Check if it's a Log sheet and matches one of our target months
        if sheet_name.endswith(" Log"):
            month_year = sheet_name.replace(" Log", "")
            if month_year in target_months:
                log_sheets.append(sheet_name)

    print(f"Found {len(log_sheets)} matching Log sheets: {', '.join(log_sheets)}")
    print()

    # Collect access data by user (aggregating across all their fobs)
    user_access_count = defaultdict(int)
    user_last_access = {}  # Track last access timestamp for each user
    total_records = 0
    fobs_not_found = set()

    for sheet_name in log_sheets:
        print(f"Processing: {sheet_name}")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Convert timestamp to datetime
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

        # Count all FOB codes in these sheets
        print(f"  Found {len(df)} records")
        total_records += len(df)

        # Count access by user (aggregating across all fobs)
        for _, row in df.iterrows():
            fob_code = row["Fob #"]
            timestamp = row["Timestamp"]

            if pd.notna(fob_code):
                # Format FOB code as 10-digit zero-padded string
                fob_code_str = str(int(fob_code)).zfill(10)

                # Find the user for this fob code
                account_id = fob_to_user.get(fob_code_str)

                if account_id:
                    user_access_count[account_id] += 1

                    # Update last access date if this is more recent
                    if pd.notna(timestamp):
                        if (
                            account_id not in user_last_access
                            or timestamp > user_last_access[account_id]
                        ):
                            user_last_access[account_id] = timestamp
                else:
                    # Track FOBs that aren't in users.json
                    fobs_not_found.add(fob_code_str)

    print(f"\nTotal records processed: {total_records}")
    if fobs_not_found:
        print(f"Warning: {len(fobs_not_found)} FOB codes not found in users.json")

    print("\n" + "=" * 60)
    print(f"User Access Summary (Last {args.months + 1} Months)")
    print("=" * 60)
    print(f"Total unique users with access: {len(user_access_count)}")
    print(f"Total access events: {sum(user_access_count.values())}")

    # Prepare user data for CSV output
    user_records = []
    for account_id, access_count in user_access_count.items():
        user = users_by_account_id.get(account_id)
        if user:
            last_access = user_last_access.get(account_id)
            user_records.append(
                {
                    "account_id": account_id,
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "preferred_name": user.get("preferred_name", ""),
                    "full_name": user.get("full_name", ""),
                    "access_count": access_count,
                    "last_access_date": (
                        last_access.strftime("%Y-%m-%d") if last_access else ""
                    ),
                }
            )

    # Sort by access_count descending
    user_records.sort(
        key=lambda x: (-x["access_count"], x["last_name"], x["first_name"])
    )

    # Write main report to CSV
    output_file = "fob_access_report.csv"
    fieldnames = [
        "account_id",
        "first_name",
        "last_name",
        "preferred_name",
        "full_name",
        "access_count",
        "last_access_date",
    ]

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(user_records)

    print(f"\nResults written to {output_file}")
    print(f"Total {len(user_records)} users with access recorded")

    # Create top users report
    # Filter to only users with one fob code if requested (before selecting top N)
    if args.only_one_fob:
        filtered_records = [
            user
            for user in user_records
            if len(users_by_account_id[user["account_id"]].get("fob_codes", [])) == 1
        ]
        top_users = filtered_records[: args.top]
    else:
        top_users = user_records[: args.top]

    # Sort top users by last name, first name
    top_users.sort(key=lambda x: (x["last_name"], x["first_name"]))

    top_output_file = "top_users.csv"
    with open(top_output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(top_users)

    filter_msg = (
        " (filtered to users with only one fob code)" if args.only_one_fob else ""
    )
    print(
        f"Top {len(top_users)} users written to {top_output_file}{filter_msg} "
        f"(sorted by last name, first name)"
    )


if __name__ == "__main__":
    main()
