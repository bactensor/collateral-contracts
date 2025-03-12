#!/usr/bin/env python3

import os
import sys
from web3 import Web3
from eth_account import Account
from address_conversion import ss58_to_pubkey
from common import get_web3_connection, get_account


def send_tao_to_ss58(w3: Web3, sender_account: Account, recipient_ss58: str, amount_wei: int) -> dict:
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
    contract_address = '0x0000000000000000000000000000000000000800'
    abi = [
        {
            "inputs": [
                {
                    "internalType": "bytes32",
                    "name": "data",
                    "type": "bytes32"
                }
            ],
            "name": "transfer",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    contract = w3.eth.contract(address=contract_address, abi=abi)
    # Convert SS58 address to public key bytes32
    pubkey = ss58_to_pubkey(recipient_ss58)
    
    # Prepare transaction
    nonce = w3.eth.get_transaction_count(sender_account.address)
    gas_price = w3.eth.gas_price

    # Build transaction
    transaction = contract.functions.transfer(pubkey).build_transaction({
        'from': sender_account.address,
        'value': amount_wei,
        'gas': 100000,
        'gasPrice': gas_price,
        'nonce': nonce,
    })

    # Sign and send transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, sender_account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction sent! Hash: {tx_hash.hex()}")

    # Wait for transaction receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


def main():
    if len(sys.argv) != 3:
        print("Usage: python send_to_ss58.py <recipient_ss58_address> <amount_wei>")
        sys.exit(1)
    recipient_ss58_address = sys.argv[1]
    amount_wei = int(sys.argv[2])

    try:
        # Initialize Web3 and account using common functions
        w3 = get_web3_connection()
        account = get_account()
        print(f"Using account: {account.address}")

        # Send transaction
        receipt = send_tao_to_ss58(
            w3=w3,
            sender_account=account,
            recipient_ss58=recipient_ss58_address,
            amount_wei=amount_wei
        )
        
        print(f"Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"Gas used: {receipt['gasUsed']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
