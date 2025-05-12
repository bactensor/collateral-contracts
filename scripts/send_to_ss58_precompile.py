#!/usr/bin/env python3

"""
SS58 Precompile Transfer Script

This script enables sending TAO tokens to SS58 addresses using the precompile
contract at address 0x0000000000000000000000000000000000000800. It handles
the conversion of SS58 addresses to the appropriate format for the precompile.
"""

import argparse
import sys
from web3 import Web3
from eth_account import Account
import bittensor.utils
from address_conversion import ss58_to_pubkey
from common import get_web3_connection, get_account, wait_for_receipt, build_and_send_transaction


def send_tao_to_ss58(
    w3: Web3, sender_account: Account, recipient_ss58: str, amount_wei: int
) -> dict:
    """
    Send TAO tokens to an SS58 address.

    Args:
        w3: Web3 instance
        sender_account: Account instance of the sender
        recipient_ss58: Recipient's SS58 address
        amount_wei: Amount to send in wei

    Returns:
        dict: Transaction receipt
    """
    contract_address = "0x0000000000000000000000000000000000000800"
    abi = [
        {
            "inputs": [{"internalType": "bytes32", "name": "data", "type": "bytes32"}],
            "name": "transfer",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function",
        }
    ]
    contract = w3.eth.contract(address=contract_address, abi=abi)
    pubkey = ss58_to_pubkey(recipient_ss58)

    tx_hash = build_and_send_transaction(
        w3,
        contract.functions.transfer(pubkey),
        sender_account,
        value=amount_wei,
    )

    # Wait for transaction receipt
    receipt = wait_for_receipt(w3, tx_hash)

    return receipt


def main():
    parser = argparse.ArgumentParser(
        description="Send TAO tokens to an SS58 address using the precompile contract"
    )
    parser.add_argument(
        "--recipient-ss58-address",
        required=True,
        help="The SS58 address of the recipient"
    )
    parser.add_argument(
        "--amount-wei",
        required=True,
        type=int,
        help="The amount to send in wei (smallest unit of TAO)"
    )
    parser.add_argument("--keyfile", help="Path to keypair file")
    parser.add_argument(
        "--network",
        default="finney",
        help="The Subtensor Network to connect to.",
    )
    args = parser.parse_args()

    w3 = get_web3_connection(args.network)
    account = get_account(args.keyfile)
    print(f"Using account: {account.address}")

    receipt = send_tao_to_ss58(
        w3=w3,
        sender_account=account,
        recipient_ss58=args.recipient_ss58_address,
        amount_wei=args.amount_wei,
    )

    print(
        f"Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}"
    )
    print(f"Gas used: {receipt['gasUsed']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
