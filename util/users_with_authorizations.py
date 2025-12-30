#!/usr/bin/env python3
"""
Extract all users with any authorizations and output to CSV.
Includes account_id, full_name, and their list of authorizations.
"""

import csv
import json


def main():
    # Read the users.json file
    with open("users.json") as f:
        users = json.load(f)

    # Filter users who have any authorizations
    users_with_auth = []
    for user in users:
        authorizations = user.get("authorizations", [])
        if authorizations:
            fob_codes = user.get("fob_codes", [])
            # Format FOB code as 10-digit zero-padded string
            if fob_codes:
                fob_code = str(fob_codes[0]).zfill(10)
                # Create CSV string of additional FOB codes (beyond the first)
                additional_fobs = [str(fc).zfill(10) for fc in fob_codes[1:]]
                fob_csv = ", ".join(additional_fobs)
            else:
                fob_code = ""
                fob_csv = ""
            users_with_auth.append(
                {
                    "account_id": user.get("account_id", ""),
                    "full_name": user.get("full_name", ""),
                    "fob_code": fob_code,
                    "FobCSV": fob_csv,
                    "authorizations": ", ".join(sorted(authorizations)),
                }
            )

    # Sort by full_name
    users_with_auth.sort(key=lambda x: x["full_name"])

    # Write to CSV
    output_file = "users_with_authorizations.csv"
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["account_id", "full_name", "fob_code", "FobCSV", "authorizations"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(users_with_auth)

    print(f"Found {len(users_with_auth)} users with authorizations")
    print(f"Results written to {output_file}")


if __name__ == "__main__":
    main()
