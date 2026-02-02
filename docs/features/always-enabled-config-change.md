# Always Enabled Config Change Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Earlier today we had a number of machines with `always_enabled` set to true in the `machines.json` configuration, which resulted in them always having their LED green and relay enabled. I changed the `machines.json` config to remove `always_enabled` (default false) to enable proper RFID-based authorization on these machines, but they stayed in the enabled state until an RFID card change was made. We need to fix this behavior, including adding unit tests to ensure we don't have a regression.
