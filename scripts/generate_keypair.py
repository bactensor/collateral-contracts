#!/usr/bin/env python3

"""
Keypair Generation Script

This script generates a new Ethereum keypair (private key, public key, and address)
and saves it to a specified file. It's useful for creating new accounts for
interacting with the Collateral smart contract.
"""

import argparse
import pathlib
import sys
import json
from eth_account import Account
from eth_keys import keys


def generate_and_save_keypair(output_path: pathlib.Path, overwrite: bool = False) -> dict:
    """
    Generate a new Ethereum key pair and save it to a file.

    Args:
        output_path (pathlib.Path): Path where the key pair should be saved.
        overwrite (bool, optional): Whether to overwrite an existing file. Defaults to False.

    Returns:
        dict: Dictionary containing the account address, private key, and public key
    """
    output_path = output_path.expanduser().resolve()
    account = Account.create()
    private_key = keys.PrivateKey(account.key)
    public_key = private_key.public_key

    keypair_data = {
        "address": account.address,
        "private_key": account.key.hex(),
        "public_key": public_key.to_hex(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w" if overwrite else "x") as f:
        json.dump(keypair_data, f, indent=2)
    print(f"Key pair saved to: {output_path}", file=sys.stderr)
    print(f"Address: {account.address}", file=sys.stderr)
    print(f"Public Key: {public_key.to_hex()}", file=sys.stderr)
    return keypair_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the existing H160 file with the new one.",
    )
    parser.add_argument(
        "output_path",
        type=pathlib.Path,
        help="Absolute path where the key pair should be saved",
    )
    args = parser.parse_args()

    try:
        generate_and_save_keypair(args.output_path, args.overwrite)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
