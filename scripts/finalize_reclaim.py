#!/usr/bin/env python3

"""
Reclaim Finalization Script

This script allows users to finalize their collateral reclaim requests after
the waiting period has elapsed. It processes the reclaim request and returns
the collateral to the user's address.
"""

import sys
import argparse
from common import (
    load_contract_abi,
    get_web3_connection,
    get_account,
    validate_address_format,
    build_and_send_transaction,
    wait_for_receipt,
)


def finalize_reclaim(w3, account, reclaim_request_id, contract_address):
    """Finalize a reclaim request on the contract.

    Args:
        w3: Web3 instance
        account: Account to use for the transaction
        reclaim_request_id: ID of the reclaim request to finalize
        contract_address: Address of the contract

    Returns:
        tuple: (reclaim_event, receipt)
    """
    validate_address_format(contract_address)

    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    tx_hash = build_and_send_transaction(
        w3,
        contract.functions.finalizeReclaim(reclaim_request_id),
        account,
    )

    receipt = wait_for_receipt(w3, tx_hash)
    reclaim_events = contract.events.Reclaimed().process_receipt(receipt)

    reclaim_event = contract.events.Reclaimed().process_receipt(receipt)[0]

    return reclaim_event, receipt


def main():
    parser = argparse.ArgumentParser(
        description="Finalize a reclaim request on the Collateral contract"
    )
    parser.add_argument(
        "contract_address", help="Address of the deployed Collateral contract"
    )
    parser.add_argument(
        "reclaim_request_id", type=int, help="ID of the reclaim request to finalize"
    )
    args = parser.parse_args()

    w3 = get_web3_connection()
    account = get_account()

    reclaim_event, receipt = finalize_reclaim(
        w3=w3,
        account=account,
        reclaim_request_id=args.reclaim_request_id,
        contract_address=args.contract_address,
    )

    print(f"Successfully finalized reclaim request {args.reclaim_request_id}")
    print("Event details:")
    print(f"  Reclaim ID: {reclaim_event['args']['reclaimRequestId']}")
    print(f"  Account: {reclaim_event['args']['account']}")
    print(
        f"  Amount: {w3.from_wei(reclaim_event['args']['amount'], 'ether')} TAO")
    print(f"  Transaction hash: {receipt['transactionHash'].hex()}")
    print(f"  Block number: {receipt['blockNumber']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
