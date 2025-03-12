#!/usr/bin/env python3

import argparse
import sys

from common import (
    get_web3_connection,
    load_contract_abi,
    validate_address_format,
)


def get_miner_collateral(w3, contract_address, miner_address):
    """Query the collateral amount for a given miner address.

    Args:
        w3: Web3 instance
        contract_address: Address of the Collateral contract
        miner_address: Address of the miner to query

    Returns:
        number: Collateral amount in Wei

    Raises:
        SystemExit: If there's an error querying the collateral
    """
    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    
    try:
        return contract.functions.collaterals(miner_address).call()
    except Exception as e:
        print(f"Error querying collateral: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to handle command line arguments and display collateral."""
    parser = argparse.ArgumentParser(
        description='Query miner collateral from the Collateral contract'
    )
    parser.add_argument('contract_address', help='Address of the Collateral contract')
    parser.add_argument('miner_address', help='Address of the miner')
    
    args = parser.parse_args()
    
    validate_address_format(args.contract_address)
    validate_address_format(args.miner_address)

    w3 = get_web3_connection()
    
    collateral = get_miner_collateral(w3, args.contract_address, args.miner_address)
    print(f"Collateral for miner {args.miner_address}: {w3.from_wei(collateral, 'ether')} TAO")


if __name__ == '__main__':
    main()
