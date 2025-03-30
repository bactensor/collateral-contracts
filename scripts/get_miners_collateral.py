#!/usr/bin/env python3

<<<<<<< HEAD
import argparse
=======
>>>>>>> 99ec69217d556a9981a40a68e1b618aa92aa09c9
import sys

from common import (
    get_web3_connection,
<<<<<<< HEAD
    load_contract_abi,
=======
    get_miner_collateral,
>>>>>>> 99ec69217d556a9981a40a68e1b618aa92aa09c9
    validate_address_format,
)


<<<<<<< HEAD
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


=======
>>>>>>> 99ec69217d556a9981a40a68e1b618aa92aa09c9
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
    print(f"Collateral for miner {miner_address}: {w3.from_wei(collateral, 'ether')} TAO")


if __name__ == '__main__':
    main()
