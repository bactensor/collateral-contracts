#!/usr/bin/env python3

import os
import sys
import json
from web3 import Web3
from eth_keys import keys


def generate_keypair() -> dict:
    """
    Generate a new Ethereum key pair.

    Returns:
        dict: Dictionary containing the public key and private key
    """
    # Generate a new account
    account = Web3().eth.account.create()
    private_key = keys.PrivateKey(account.key)
    public_key = private_key.public_key.to_hex()
    
    # Prepare the key pair data
    keypair_data = {
        "public_key": public_key,
        "private_key": account.key.hex()
    }
    
    return keypair_data


def save_keypair(keypair_data: dict, output_path: str) -> None:
    """
    Save a key pair to a file.

    Args:
        keypair_data (dict): Dictionary containing the public key and private key
        output_path (str): Relative path where the key pair should be saved

    Raises:
        Exception: If there's an error saving the file
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_output_path = os.path.join(script_dir, output_path)
    os.makedirs(os.path.dirname(absolute_output_path), exist_ok=True)

    try:
        with open(absolute_output_path, "w") as f:
            json.dump(keypair_data, f, indent=2)
        print(f"Public key: {keypair_data['public_key']}", file=sys.stderr)
    except Exception as e:
        print(f"Error saving key pair: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_keypair.py <output_path>")
        print("Example: python generate_keypair.py keys/account.json")
        sys.exit(1)

    output_path = sys.argv[1]
    keypair_data = generate_keypair()
    save_keypair(keypair_data, output_path)


if __name__ == "__main__":
    main()
