#!/usr/bin/env python3

"""
Miner Collateral Query Tool

This script allows users to query the collateral amount for a specific miner
in a given smart contract. It connects to a blockchain network, validates
the provided addresses, and retrieves the collateral information.

The script will output the collateral amount in TAO (the native token).
"""

import sys

from common import (
    get_web3_connection,
    get_miner_collateral,
    validate_address_format,
)


def main():
    """Main function to handle command line arguments and display collateral."""
    if len(sys.argv) != 3:
        print(
            "Usage: python get_miners_collateral.py <contract_address> <miner_address>",
            file=sys.stderr,
        )
        print(
            "Example: python get_miners_collateral.py 0x123... 0x456... ",
            file=sys.stderr,
        )
        sys.exit(1)
    contract_address = sys.argv[1]
    miner_address = sys.argv[2]

    validate_address_format(contract_address)
    validate_address_format(miner_address)

    w3 = get_web3_connection()

    collateral = get_miner_collateral(w3, contract_address, miner_address)
    print(
        f"Collateral for miner {miner_address}: {w3.from_wei(collateral, 'ether')} TAO"
    )


if __name__ == "__main__":
    main()
