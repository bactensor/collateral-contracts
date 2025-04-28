#!/usr/bin/env python3

"""
Keypair Generation Script

This script generates a new Ethereum keypair (private key, public key, and address)
and saves it to a specified file. It's useful for creating new accounts for
interacting with the Collateral smart contract.
"""

import os
import sys
import json
from eth_account import Account
from eth_keys import keys


def generate_and_save_keypair(output_path: str) -> dict:
    """
    Generate a new Ethereum key pair and save it to a file.

    Args:
        output_path (str): Absolute path where the key pair should be saved

    Returns:
        dict: Dictionary containing the account address, private key, and public key

    Raises:
        Exception: If there's an error saving the file
    """
    account = Account.create()
    private_key = keys.PrivateKey(account.key)
    public_key = private_key.public_key

    keypair_data = {
        "address": account.address,
        "private_key": account.key.hex(),
        "public_key": public_key.to_hex()
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(keypair_data, f, indent=2)
    print(f"Key pair saved to: {output_path}", file=sys.stderr)
    print(f"Address: {account.address}", file=sys.stderr)
    print(f"Public Key: {public_key.to_hex()}", file=sys.stderr)
    return keypair_data


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_keypair.py <output_path>")
        print("Example: python generate_keypair.py keys/account.json")
        sys.exit(1)

    output_path = sys.argv[1]
    generate_and_save_keypair(output_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
