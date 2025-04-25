#!/usr/bin/env python3

"""
Miner Collateral Query Tool

This script allows users to query the collateral amount for a specific miner
in a given smart contract. It connects to a blockchain network, validates
the provided addresses, and retrieves the collateral information.

The script will output the collateral amount in TAO (the native token).
"""

import argparse
import sys
from common import (
    get_web3_connection,
    get_miner_collateral,
    validate_address_format,
)


def main():
    """Main function to handle command line arguments and display collateral."""
    parser = argparse.ArgumentParser(
        description="Query the collateral amount for a specific miner in a smart contract"
    )
    parser.add_argument(
        "contract_address",
        help="The address of the smart contract"
    )
    parser.add_argument(
        "miner_address",
        help="The address of the miner to query"
    )
    
    args = parser.parse_args()
    
    validate_address_format(args.contract_address)
    validate_address_format(args.miner_address)

    w3 = get_web3_connection()

    collateral = get_miner_collateral(w3, args.contract_address, args.miner_address)
    print(
        f"Collateral for miner {args.miner_address}: {w3.from_wei(collateral, 'ether')} TAO"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
