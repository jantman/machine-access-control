#!/usr/bin/env python3
"""
Combine users_with_authorizations.csv with fob_access_report.csv
Creates a merged report showing users with their authorizations and access statistics.
"""

import csv


def main():
    # Read fob_access_report.csv into a dictionary
    fob_access = {}
    with open("fob_access_report.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fob_code = row["fob_code"]
            fob_access[fob_code] = {
                "access_count": row["access_count"],
                "last_access_date": row["last_access_date"],
            }

    # Read users_with_authorizations.csv and merge with access data
    combined_users = []
    with open("users_with_authorizations.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fob_code = row["fob_code"]

            # Get access info if available
            if fob_code and fob_code in fob_access:
                access_info = fob_access[fob_code]
                row["access_count"] = access_info["access_count"]
                row["last_access_date"] = access_info["last_access_date"]
            else:
                row["access_count"] = "0"
                row["last_access_date"] = ""

            combined_users.append(row)

    # Sort by access_count (descending), then by full_name
    combined_users.sort(
        key=lambda x: (
            -int(x["access_count"]) if x["access_count"].isdigit() else 0,
            x["full_name"],
        )
    )

    # Write to CSV
    output_file = "common_users.csv"
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = [
            "account_id",
            "full_name",
            "fob_code",
            "FobCSV",
            "access_count",
            "last_access_date",
            "authorizations",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(combined_users)

    # Print summary
    users_with_access = sum(1 for u in combined_users if int(u["access_count"]) > 0)
    users_without_access = len(combined_users) - users_with_access

    print("Combined user and access data")
    print("=" * 60)
    print(f"Total users with authorizations: {len(combined_users)}")
    print(f"  Users with access in analyzed period: {users_with_access}")
    print(f"  Users without access in analyzed period: {users_without_access}")
    print(f"\nResults written to {output_file}")


if __name__ == "__main__":
    main()
