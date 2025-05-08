#!/usr/bin/env python3

"""
Collateral Reclaim Script

This script allows users to initiate the process of reclaiming their collateral
from the Collateral smart contract. It handles the creation of reclaim requests
with associated URLs for verification purposes.
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
    calculate_md5_checksum,
    get_revert_reason,
)


class ReclaimCollateralError(Exception):
    """Exception raised when there is an error during the collateral reclaim process."""
    pass


def reclaim_collateral(
    w3,
    account,
    amount_tao,
    contract_address,
    url,
):
    """Reclaim collateral from the contract.

    Args:
        w3 (Web3): Web3 instance
        account: The account to use for the transaction
        amount_tao (float): Amount of TAO to reclaim
        contract_address (str): Address of the collateral contract
        url (str): URL for reclaim information

    Returns:
        dict: Transaction receipt with reclaim event details

    Raises:
        Exception: If the transaction fails
    """
    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    amount_wei = w3.to_wei(amount_tao, "ether")

    # Calculate MD5 checksum if URL is valid
    md5_checksum = "0" * 32
    if url.startswith(("http://", "https://")):
        print("Calculating MD5 checksum of URL content...", file=sys.stderr)
        md5_checksum = calculate_md5_checksum(url)
        print(f"MD5 checksum: {md5_checksum}", file=sys.stderr)

    tx_hash = build_and_send_transaction(
        w3,
        contract.functions.reclaimCollateral(
            amount_wei,
            url,
            bytes.fromhex(md5_checksum),
        ),
        account,
        gas_limit=200000,  # Higher gas limit for this function
    )

    receipt = wait_for_receipt(w3, tx_hash)
    if receipt['status'] == 0:
        revert_reason = get_revert_reason(w3, tx_hash, receipt['blockNumber'])
        raise ReclaimCollateralError(f"Transaction failed for reclaiming collateral. Revert reason: {revert_reason}")
    reclaim_event = contract.events.ReclaimProcessStarted().process_receipt(
        receipt,
    )[0]

    return receipt, reclaim_event


def main():
    parser = argparse.ArgumentParser(
        description="Initiate the process of reclaiming collateral."
    )
    parser.add_argument(
        "--contract-address",
        required=True,
        help="Address of the collateral contract"
    )
    parser.add_argument(
        "--amount-tao",
        required=True,
        type=float,
        help="Amount of TAO to reclaim"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL for reclaim information"
    )
    parser.add_argument("--keyfile", help="Path to keypair file")
    parser.add_argument(
        "--network",
        default="finney",
        help="The Subtensor Network to connect to.",
    )

    args = parser.parse_args()

    validate_address_format(args.contract_address)

    _, network_url = bittensor.utils.determine_chain_endpoint_and_network(args.network)
    w3 = get_web3_connection(network_url)
    account = get_account(args.keyfile)

    receipt, event = reclaim_collateral(
        w3, account, args.amount_tao, args.contract_address, args.url)

    print(f"Successfully initiated reclaim of {args.amount_tao} TAO")
    print("Event details:")
    print(f"  Reclaim ID: {event['args']['reclaimRequestId']}")
    print(f"  Account: {event['args']['account']}")
    print(
        f"  Amount: "
        f"{w3.from_wei(event['args']['amount'], 'ether')} TAO",
    )
    print(
        f"  Expiration Time: {event['args']['expirationTime']}")
    print(f"  URL: {event['args']['url']}")
    print(
        f"  URL Content MD5: "
        f"{event['args']['urlContentMd5Checksum'].hex()}",
    )
    print(
        f"  Transaction hash: {receipt['transactionHash'].hex()}")
    print(f"  Block number: {receipt['blockNumber']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
