#!/usr/bin/env python3

import sys
import hashlib
import requests

from web3 import Web3
from common import (
    load_contract_abi,
    get_web3_connection,
    get_account,
    validate_address_format,
    build_and_send_transaction,
    wait_for_receipt,
)


def calculate_md5_checksum(url):
    """Calculate MD5 checksum of the content at the given URL.
    
    Args:
        url (str): The URL to fetch content from.
        
    Returns:
        str: The MD5 checksum of the content.
        
    Raises:
        SystemExit: If there's an error fetching the URL content.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return hashlib.md5(response.content).hexdigest()
    except requests.RequestException as e:
        print(f"Error fetching URL content: {str(e)}", file=sys.stderr)
        sys.exit(1)


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
    # Load contract ABI and create contract instance
    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # Convert amount to wei
    amount_wei = w3.to_wei(amount_tao, 'ether')

    # Calculate MD5 checksum if URL is valid
    md5_checksum = '0' * 32
    if url.startswith(('http://', 'https://')):
        print("Calculating MD5 checksum of URL content...", file=sys.stderr)
        md5_checksum = calculate_md5_checksum(url)
        print(f"MD5 checksum: {md5_checksum}", file=sys.stderr)

    # Build and send transaction
    tx_hash = build_and_send_transaction(
        w3,
        contract,
        contract.functions.reclaimCollateral(
            amount_wei,
            url,
            bytes.fromhex(md5_checksum),
        ),
        account,
        gas_limit=200000,  # Higher gas limit for this function
    )

    # Wait for receipt
    receipt = wait_for_receipt(w3, tx_hash)

    # Get the ReclaimProcessStarted event from the receipt
    reclaim_event = contract.events.ReclaimProcessStarted().process_receipt(
        receipt,
    )[0]

    return {
        'receipt': receipt,
        'event': reclaim_event,
        'amount_tao': amount_tao,
    }


def main():
    # Check command line arguments
    if len(sys.argv) != 4:
        print(
            "Usage: python reclaim_collateral.py "
            "<contract_address> <amount_in_tao> <url>",
            file=sys.stderr,
        )
        print(
            "Example: python reclaim_collateral.py "
            "0x123... 1.5 https://example.com/reclaim-info",
            file=sys.stderr,
        )
        sys.exit(1)

    contract_address = sys.argv[1]
    amount_tao = float(sys.argv[2])
    url = sys.argv[3]

    # Validate contract address
    validate_address_format(contract_address)

    # Get Web3 connection and account
    w3 = get_web3_connection()
    account = get_account()

    try:
        result = reclaim_collateral(w3, account, amount_tao, contract_address, url)
        
        # Print success message with event details
        print(f"Successfully initiated reclaim of {result['amount_tao']} TAO")
        print("Event details:")
        print(f"  Reclaim ID: {result['event']['args']['reclaimRequestId']}")
        print(f"  Account: {result['event']['args']['account']}")
        print(
            f"  Amount: "
            f"{w3.from_wei(result['event']['args']['amount'], 'ether')} TAO",
        )
        print(f"  Expiration Time: {result['event']['args']['expirationTime']}")
        print(f"  URL: {result['event']['args']['url']}")
        print(
            f"  URL Content MD5: "
            f"{result['event']['args']['urlContentMd5Checksum'].hex()}",
        )
        print(f"  Transaction hash: {result['receipt']['transactionHash'].hex()}")
        print(f"  Block number: {result['receipt']['blockNumber']}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
    