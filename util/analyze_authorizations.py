#!/usr/bin/env python3
"""
Analyze authorizations from users.json file.
Reports all distinct values of the 'authorizations' field along with the count of users having each.
"""

import json
from collections import Counter


def main():
    # Read the users.json file
    with open("users.json") as f:
        users = json.load(f)

    # Collect all authorization values
    authorization_counter = Counter()

    for user in users:
        authorizations = user.get("authorizations", [])
        # Count each authorization
        for auth in authorizations:
            authorization_counter[auth] += 1

    # Print results
    print("Authorization Analysis")
    print("=" * 60)
    print(f"Total users: {len(users)}")
    print(f"Total distinct authorizations: {len(authorization_counter)}")
    print()
    print("Authorization Counts (sorted by count, descending):")
    print("-" * 60)

    # Sort by count (descending), then by name (ascending)
    for auth, count in sorted(
        authorization_counter.items(), key=lambda x: (-x[1], x[0])
    ):
        print(f"{count:4d}  {auth}")

    print("-" * 60)
    print(
        f"Total: {sum(authorization_counter.values())} authorizations across all users"
    )


if __name__ == "__main__":
    main()
