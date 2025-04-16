#!/usr/bin/env python3

"""
Collateral Slashing Script

This script allows trustees to slash collateral from miners who have violated
protocol rules. It handles the creation of slashing requests with associated
URLs for verification purposes.
"""

import sys
from common import (
    load_contract_abi,
    get_web3_connection,
    get_account,
    validate_address_format,
    build_and_send_transaction,
    wait_for_receipt,
    calculate_md5_checksum,
)


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
    slash_event = contract.events.Slashed().process_receipt(receipt)[0]

    return {
        "receipt": receipt,
        "event": slash_event,
    }


def main():
    if len(sys.argv) != 5:
        print(
            "Usage: python slash_collateral.py "
            "<contract_address> <miner_address> <amount_in_tao> <url>",
            file=sys.stderr,
        )
        print(
            "Example: python slash_collateral.py "
            "0x123... 0x456... 1.5 https://example.com/slash-info",
            file=sys.stderr,
        )
        sys.exit(1)

    contract_address = sys.argv[1]
    miner_address = sys.argv[2]
    amount_tao = float(sys.argv[3])
    url = sys.argv[4]

    validate_address_format(contract_address)
    validate_address_format(miner_address)

    w3 = get_web3_connection()
    account = get_account()

    try:
        result = slash_collateral(
            w3,
            account,
            miner_address,
            amount_tao,
            contract_address,
            url,
        )

        print(f"Successfully slashed {amount_tao} TAO from {miner_address}")
        print("Event details:")
        print(f"  Account: {result['event']['args']['account']}")
        print(
            f"  Amount: "
            f"{w3.from_wei(result['event']['args']['amount'], 'ether')} TAO",
        )
        print(f"  URL: {result['event']['args']['url']}")
        print(
            f"  URL Content MD5: "
            f"{result['event']['args']['urlContentMd5Checksum'].hex()}",
        )
        print(
            f"  Transaction hash: {result['receipt']['transactionHash'].hex()}")
        print(f"  Block number: {result['receipt']['blockNumber']}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
