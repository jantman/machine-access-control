#!/usr/bin/env python
# flake8: noqa
# mypy: ignore-errors
"""Script to sanitize responses YAML files."""

import argparse
import json
import logging
import random
import string
import sys
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from typing import cast

from faker import Faker
from faker.providers import internet
from yaml import dump
from yaml import load

from dm_mac.neongetter import NeonUserUpdater
from dm_mac.utils import load_json_config


try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper
    from yaml import Loader

logging.basicConfig(
    level=logging.WARNING, format="[%(asctime)s %(levelname)s] %(message)s"
)
logger: logging.Logger = logging.getLogger()


class NeonSanitizer:
    """Sanitize Neon responses files."""

    def __init__(self):
        """Initialize class."""
        self._neon_config: Dict[str, Union[str, List[str]]] = cast(
            Dict[str, Union[str, List[str]]],
            load_json_config("NEONGETTER_CONFIG", "neon.config.json"),
        )
        NeonUserUpdater.validate_config(self._neon_config)
        self.full_name_fields: List[str] = [self._neon_config["full_name_field"]]
        self.first_name_fields: List[str] = [
            self._neon_config["first_name_field"],
        ]
        self.last_name_fields: List[str] = [
            self._neon_config["last_name_field"],
        ]
        self.preferred_name_fields: List[str] = [
            self._neon_config["preferred_name_field"],
        ]
        self.email_fields: List[str] = [self._neon_config["email_field"]]
        self.acct_id_field: str = self._neon_config["account_id_field"]
        self.tendigit_fields: List[str] = self._neon_config["fob_fields"]
        self.acct_id: int = 1
        self.fake: Faker = Faker()
        self.fake.add_provider(internet)
        self.fobs: List[str] = []

    def _random_fob_tendigit(self) -> str:
        """Generate and return a random fob code."""
        while True:
            s: str = "".join(random.choices(string.digits, k=10))
            if s not in self.fobs:
                self.fobs.append(s)
                return s

    def sanitize(self, input: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize an item."""
        result: List[Dict[str, Any]] = []
        for item in input:
            f = self.fake.unique
            # account ID
            if self.acct_id_field in item:
                item[self.acct_id_field] = str(self.acct_id)
                self.acct_id += 1
            fname: str
            # names
            for fname in self.full_name_fields:
                if fname not in item:
                    continue
                item[fname] = f.name()
            for fname in self.first_name_fields:
                if fname not in item:
                    continue
                item[fname] = item[self.full_name_fields[0]].split(" ")[0]
            for fname in self.last_name_fields:
                if fname not in item:
                    continue
                item[fname] = item[self.full_name_fields[0]].split(" ")[-1]
            for fname in self.preferred_name_fields:
                if fname not in item:
                    continue
                item[fname] = "P" + item[self.full_name_fields[0]].split(" ")[0]
            # email
            for fname in self.email_fields:
                if fname not in item:
                    continue
                item[fname] = f.email()
            # fob
            for fname in self.tendigit_fields:
                if fname not in item:
                    continue
                item[fname] = self._random_fob_tendigit()
            result.append(item)
        return result

    def run(self, in_file: str, out_file: str) -> None:
        """Run it."""
        with open(in_file) as fh:
            input: Dict[str, List[Dict[Any]]] = load(fh, Loader=Loader)
        result: List[Dict[Any]] = []
        for idx, item in enumerate(input["responses"]):
            if "body" not in item["response"]:
                print(f"No body in item {idx}")
                result.append(item)
                continue
            try:
                body = json.loads(item["response"]["body"])
                assert "searchResults" in body
            except Exception:
                print(f"No JSON body in item {idx}")
                result.append(item)
                continue
            body["searchResults"] = self.sanitize(body["searchResults"])
            item["response"]["body"] = json.dumps(body)
            result.append(item)
        with open(out_file, "w") as fh:
            dump({"responses": result}, fh, Dumper=Dumper)
        print(f"Wrote: {out_file}")


def main() -> None:
    """Main entrypoint for CLI script."""
    p = argparse.ArgumentParser(description="Sanitize neon responses")
    p.add_argument("ORIGINAL", type=str, help="Original YAML file path")
    p.add_argument("SANITIZED", type=str, help="Sanitized YAML output path")
    args = p.parse_args(sys.argv[1:])
    NeonSanitizer().run(args.ORIGINAL, args.SANITIZED)


if __name__ == "__main__":
    main()
