#!/usr/bin/env python3

"""
Reclaim Finalization Script

This script allows users to finalize their collateral reclaim requests after
the waiting period has elapsed. It processes the reclaim request and returns
the collateral to the user's address.
"""

import sys
import argparse
import bittensor.utils
from common import (
    load_contract_abi,
    get_web3_connection,
    get_account,
    validate_address_format,
    build_and_send_transaction,
    wait_for_receipt,
    get_revert_reason,
)
import json
from web3.exceptions import ContractLogicError


class FinalizeReclaimError(Exception):
    """Raised when finalizing a reclaim request fails."""
    pass


def finalize_reclaim(w3, account, reclaim_request_id, contract_address):
    """Finalize a reclaim request on the contract.

    Args:
        w3: Web3 instance
        account: Account to use for the transaction
        reclaim_request_id: ID of the reclaim request to finalize
        contract_address: Address of the contract

    Returns:
        tuple: (reclaim_event, receipt)

    Raises:
        FinalizeReclaimError: If the transaction fails for any reason
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

    if receipt['status'] == 0:
        # Try to get revert reason
        revert_reason = get_revert_reason(w3, tx_hash, receipt['blockNumber'])
        raise FinalizeReclaimError(f"Transaction failed for finalizing reclaim request {reclaim_request_id}. Revert reason: {revert_reason}")

    reclaim_event = contract.events.Reclaimed().process_receipt(receipt)[0]
    return reclaim_event, receipt


def main():
    parser = argparse.ArgumentParser(
        description="Finalize a reclaim request on the Collateral contract"
    )
    parser.add_argument(
        "--contract-address", required=True, help="Address of the deployed Collateral contract"
    )
    parser.add_argument(
        "--reclaim-request-id", required=True, type=int, help="ID of the reclaim request to finalize"
    )
    parser.add_argument("--keyfile", help="Path to keypair file")
    parser.add_argument("--network", default="finney", help="The Subtensor Network to connect to.")
    args = parser.parse_args()

    w3 = get_web3_connection(args.network)
    account = get_account(args.keyfile)

    try:
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
    except FinalizeReclaimError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
