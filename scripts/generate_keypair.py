#!/usr/bin/env python3

import os
import sys
import json
from eth_account import Account


def generate_and_save_keypair(output_path: str) -> dict:
    """
    Generate a new Ethereum key pair and save it to a file.

    Args:
        output_path (str): Path where the key pair should be saved

    Returns:
        dict: Dictionary containing the account address and private key

    Raises:
        Exception: If there's an error saving the file
    """
    account = Account.create()
    keypair_data = {"address": account.address, "private_key": account.key.hex()}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with open(output_path, "w") as f:
            json.dump(keypair_data, f, indent=2)
        print(f"Key pair saved to: {output_path}", file=sys.stderr)
        print(f"Address: {account.address}", file=sys.stderr)
        return keypair_data
    except Exception as e:
        print(f"Error saving key pair: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_keypair.py <output_path>")
        print("Example: python generate_keypair.py keys/account.json")
        sys.exit(1)

    output_path = sys.argv[1]
    generate_and_save_keypair(output_path)


if __name__ == "__main__":
    main()
