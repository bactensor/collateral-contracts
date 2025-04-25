#!/usr/bin/env python3

"""
Collateral Slashing Script

This script allows trustees to slash collateral from miners who have violated
protocol rules. It handles the creation of slashing requests with associated
URLs for verification purposes.
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


class SlashCollateralError(Exception):
    """Custom exception for errors that occur during collateral slashing operations."""
    pass


def slash_collateral(
    w3,
    account,
    miner_address,
    amount_tao,
    contract_address,
    url,
):
    """Slash collateral from a miner.

    Args:
        w3 (Web3): Web3 instance
        account: The account to use for the transaction
        miner_address (str): Address of the miner to slash
        amount_tao (float): Amount of TAO to slash
        contract_address (str): Address of the collateral contract
        url (str): URL containing information about the slash

    Returns:
        dict: Transaction receipt with slash event details

    Raises:
        Exception: If the transaction fails
    """
    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # Calculate MD5 checksum if URL is valid
    md5_checksum = "0" * 32
    if url.startswith(("http://", "https://")):
        print("Calculating MD5 checksum of URL content...", file=sys.stderr)
        md5_checksum = calculate_md5_checksum(url)
        print(f"MD5 checksum: {md5_checksum}", file=sys.stderr)

    tx_hash = build_and_send_transaction(
        w3,
        contract.functions.slashCollateral(
            miner_address,
            w3.to_wei(amount_tao, "ether"),
            url,
            bytes.fromhex(md5_checksum),
        ),
        account,
        gas_limit=200000,  # Higher gas limit for this function
    )

    receipt = wait_for_receipt(w3, tx_hash)
    if receipt['status'] == 0:
        raise SlashCollateralError(f"Transaction failed for slashing collateral")
    slash_event = contract.events.Slashed().process_receipt(receipt)[0]

    return receipt, slash_event


def main():
    parser = argparse.ArgumentParser(
        description="Slash collateral from a miner."
    )
    parser.add_argument(
        "contract_address",
        help="Address of the collateral contract"
    )
    parser.add_argument(
        "miner_address",
        help="Address of the miner to slash"
    )
    parser.add_argument(
        "amount_tao",
        type=float,
        help="Amount of TAO to slash"
    )
    parser.add_argument(
        "url",
        help="URL containing information about the slash"
    )

    args = parser.parse_args()

    validate_address_format(args.contract_address)
    validate_address_format(args.miner_address)

    w3 = get_web3_connection()
    account = get_account()

    receipt, event = slash_collateral(
        w3,
        account,
        args.miner_address,
        args.amount_tao,
        args.contract_address,
        args.url,
    )

    print(f"Successfully slashed {args.amount_tao} TAO from {args.miner_address}")
    print("Event details:")
    print(f"  Account: {event['args']['account']}")
    print(
        f"  Amount: "
        f"{w3.from_wei(event['args']['amount'], 'ether')} TAO",
    )
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
