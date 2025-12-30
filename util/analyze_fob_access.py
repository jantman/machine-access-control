#!/usr/bin/env python3
"""
Analyze FOB code access from Space Access Reports.xlsx
Lists FOB codes that have accessed the space in the last N months,
sorted by number of appearances.
"""

import argparse
import csv
from collections import Counter
from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta


def main():
    parser = argparse.ArgumentParser(
        description="Analyze FOB access from Space Access Reports"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of past months to analyze (default: 3, meaning current month + 3 past months)",
    )
    args = parser.parse_args()

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

    # Collect all FOB codes
    fob_counter = Counter()
    fob_last_access = {}  # Track last access timestamp for each FOB
    total_records = 0

    for sheet_name in log_sheets:
        print(f"Processing: {sheet_name}")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Convert timestamp to datetime
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

        # Count all FOB codes in these sheets
        print(f"  Found {len(df)} records")
        total_records += len(df)

        # Count FOB codes and track last access
        for _, row in df.iterrows():
            fob_code = row["Fob #"]
            timestamp = row["Timestamp"]

            if pd.notna(fob_code):
                # Format FOB code as 10-digit zero-padded string
                fob_code_str = str(int(fob_code)).zfill(10)
                fob_counter[fob_code_str] += 1

                # Update last access date if this is more recent
                if pd.notna(timestamp):
                    if (
                        fob_code_str not in fob_last_access
                        or timestamp > fob_last_access[fob_code_str]
                    ):
                        fob_last_access[fob_code_str] = timestamp

    print(f"\nTotal records processed: {total_records}")

    print("\n" + "=" * 60)
    print(f"FOB Code Access Summary (Last {args.months + 1} Months)")
    print("=" * 60)
    print(f"Total unique FOB codes: {len(fob_counter)}")
    print(f"Total access events: {sum(fob_counter.values())}")

    # Sort by count (descending)
    sorted_fobs = sorted(fob_counter.items(), key=lambda x: (-x[1], x[0]))

    # Write to CSV
    output_file = "fob_access_report.csv"
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["fob_code", "access_count", "last_access_date"])
        for fob_code, count in sorted_fobs:
            last_access = fob_last_access.get(fob_code, None)
            last_access_str = last_access.strftime("%Y-%m-%d") if last_access else ""
            writer.writerow([fob_code, count, last_access_str])

    print(f"\nResults written to {output_file}")
    print(f"Total {len(sorted_fobs)} FOB codes with access recorded")


if __name__ == "__main__":
    main()
