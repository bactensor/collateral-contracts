#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from typing import Optional

from address_conversion import privkey_to_ss58


def run_btcli_command(command: list):
    """Run a btcli command and return its output.

    Args:
        command: List of command arguments

    Returns:
        tuple: (return_code, stdout, stderr)
    """
    try:
        process = subprocess.Popen(
            ["btcli"] + command,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        
        # Wait for the process to complete
        process.wait()
        
    except subprocess.SubprocessError as e:
        print(f"Error running btcli command: {str(e)}", file=sys.stderr)


def transfer_tao(
    amount: float,
    wallet_name: Optional[str] = None,
    subtensor_network: str = "local",
) :
    """Transfer TAO tokens to an address derived from a public key using btcli.

    Args:
        amount: Amount of TAO to transfer
        wallet_name: Name of the wallet to use (optional)
        subtensor_network: Network to use (default: local)

    Returns:
        bool: True if transfer was successful, False otherwise
    """
    try:
        private_key = os.environ.get("PRIVATE_KEY")
        if not private_key:
            print("Error: PRIVATE_KEY environment variable is not set", file=sys.stderr)
            return

        dest_address = privkey_to_ss58(private_key)
        print(f"Converting public key to SS58 address: {dest_address}")

        command = ["wallet", "transfer"]
        if wallet_name:
            command.extend(["--wallet.name", wallet_name])
        command.extend(["--subtensor.network", subtensor_network])
        command.extend(["--dest", dest_address, "--amount", str(amount)])

        run_btcli_command(command)

    except ValueError as e:
        print(f"Error converting public key: {str(e)}", file=sys.stderr)


def main():
    """Main function to handle command line arguments and execute transfer."""
    parser = argparse.ArgumentParser(
        description="Transfer TAO tokens to an address derived from a public key"
    )
    parser.add_argument("amount", type=float, help="Amount of TAO to transfer")
    parser.add_argument("--wallet", help="Name of the wallet to use")
    parser.add_argument(
        "--network",
        default="test",
        choices=["local", "test", "main"],
        help="Network to use (default: local)",
    )

    args = parser.parse_args()

    transfer_tao(
        amount=args.amount,
        wallet_name=args.wallet,
        subtensor_network=args.network,
    )


if __name__ == "__main__":
    main()
