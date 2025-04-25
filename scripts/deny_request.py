#!/usr/bin/env python3

"""
Reclaim Request Denial Script

This script allows trustees to deny collateral reclaim requests. It requires
a URL that explains the reason for denial, which is stored on-chain for
transparency and accountability.
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
    calculate_md5_checksum,
)


class DenyReclaimRequestError(Exception):
    """Raised when denying a reclaim request fails."""
    pass


def deny_reclaim_request(
        w3, account, reclaim_request_id, url, contract_address):
    """Deny a reclaim request on the contract.

    Args:
        w3: Web3 instance
        account: Account to use for the transaction
        reclaim_request_id: ID of the reclaim request to deny
        url: URL containing the reason for denial
        contract_address: Address of the contract

    Returns:
        tuple: (deny_event, receipt)
    """
    validate_address_format(contract_address)

    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # Calculate MD5 checksum of the URL content
    md5_checksum = "0" * 32
    if url.startswith(("http://", "https://")):
        print("Calculating MD5 checksum of URL content...", file=sys.stderr)
        md5_checksum = calculate_md5_checksum(url)
        print(f"MD5 checksum: {md5_checksum}", file=sys.stderr)

    tx_hash = build_and_send_transaction(
        w3,
        contract.functions.denyReclaimRequest(
            reclaim_request_id, url, bytes.fromhex(md5_checksum)
        ),
        account,
    )

    receipt = wait_for_receipt(w3, tx_hash)
    if receipt['status'] == 0:
        raise DenyReclaimRequestError(f"Transaction failed for denying reclaim request {reclaim_request_id}")
    deny_event = contract.events.Denied().process_receipt(receipt)[0]

    return deny_event, receipt


def main():
    parser = argparse.ArgumentParser(
        description="Deny a reclaim request on the Collateral contract"
    )
    parser.add_argument(
        "contract_address", help="Address of the deployed Collateral contract"
    )
    parser.add_argument(
        "reclaim_request_id", type=int, help="ID of the reclaim request to deny"
    )
    parser.add_argument("url", help="URL containing the reason for denial")
    args = parser.parse_args()

    w3 = get_web3_connection()
    account = get_account()

    deny_event, receipt = deny_reclaim_request(
        w3=w3,
        account=account,
        reclaim_request_id=args.reclaim_request_id,
        url=args.url,
        contract_address=args.contract_address,
    )

    print(f"Successfully denied reclaim request {args.reclaim_request_id}")
    print("Event details:")
    print(f"  Reclaim ID: {deny_event['args']['reclaimRequestId']}")
    print(f"  URL: {deny_event['args']['url']}")
    print(
        f"  URL Content MD5: {deny_event['args']['urlContentMd5Checksum'].hex()}")
    print(f"  Transaction hash: {receipt['transactionHash'].hex()}")
    print(f"  Block number: {receipt['blockNumber']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
