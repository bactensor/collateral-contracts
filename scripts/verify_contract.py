#!/usr/bin/env python3

"""
Contract Verification Script

This script verifies the Collateral smart contract on the blockchain explorer.
It works by deploying the contract on a local Anvil instance, comparing the
bytecode with the deployed contract, and submitting verification to the explorer.
"""

import argparse
import subprocess
import sys
import time
from web3 import Web3
from common import get_web3_connection

ANVIL_PORT = 8555
ANVIL_RPC_URL = f"http://127.0.0.1:{ANVIL_PORT}"
# the first preset private key available in anvil
ANVIL_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def get_contract_config(w3, contract_address):
    # minimal ABI for the functions we need
    ABI = [
        {
            "inputs": [],
            "name": "NETUID",
            "outputs": [{"internalType": "uint16", "name": "", "type": "uint16"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "TRUSTEE",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "DECISION_TIMEOUT",
            "outputs": [{"internalType": "uint64", "name": "", "type": "uint64"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "MIN_COLLATERAL_INCREASE",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    contract = w3.eth.contract(address=contract_address, abi=ABI)

    netuid = contract.functions.NETUID().call()
    trustee = contract.functions.TRUSTEE().call()
    decision_timeout = contract.functions.DECISION_TIMEOUT().call()
    min_collateral_increase = contract.functions.MIN_COLLATERAL_INCREASE().call()

    return netuid, trustee, decision_timeout, min_collateral_increase


def get_deployed_bytecode(w3, contract_address):
    """Get the deployed contract's bytecode."""
    return w3.eth.get_code(contract_address).hex()


def deploy_on_devnet_and_get_bytecode(w3, contract_address):
    """Deploy the contract on anvil and return its bytecode."""
    netuid, trustee, decision_timeout, min_collateral_increase = get_contract_config(
        w3, contract_address
    )

    anvil_process = subprocess.Popen(
        ["anvil", "--port", str(ANVIL_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for anvil to start
        time.sleep(2)

        deploy_cmd = [
            "forge",
            "create",
            "src/Collateral.sol:Collateral",
            "--broadcast",
            "--rpc-url",
            ANVIL_RPC_URL,
            "--private-key",
            ANVIL_PRIVATE_KEY,
            "--constructor-args",
            f"{netuid}",
            f"{trustee}",
            f"{min_collateral_increase}",
            f"{decision_timeout}",
        ]

        deploy_output = subprocess.run(
            deploy_cmd, check=True, capture_output=True, text=True
        )
        deployed_address = (
            deploy_output.stdout.split("Deployed to: ")[1].strip().split()[0]
        )
        devnet_w3 = Web3(Web3.HTTPProvider(ANVIL_RPC_URL))
        return get_deployed_bytecode(devnet_w3, deployed_address)

    finally:
        anvil_process.terminate()
        anvil_process.wait()


def verify_contract(contract_address, expected_trustee, expected_netuid):
    """Verify if the deployed contract matches the source code and expected values."""
    try:
        w3 = get_web3_connection()

        # Get contract configuration
        netuid, trustee, _decision_timeout, _min_collateral_increase = get_contract_config(w3, contract_address)

        # Verify expected values if provided
        if expected_trustee is not None:
            if Web3.to_checksum_address(trustee) != Web3.to_checksum_address(expected_trustee):
                print(f"❌ Trustee verification failed!")
                print(f"Expected: {expected_trustee}")
                print(f"Actual: {trustee}")
                return False
            print(f"✅ Trustee verification successful!")

        if expected_netuid is not None:
            if int(netuid) != int(expected_netuid):
                print(f"❌ NetUID verification failed!")
                print(f"Expected: {expected_netuid}")
                print(f"Actual: {netuid}")
                return False
            print(f"✅ NetUID verification successful!")

        deployed_bytecode = get_deployed_bytecode(w3, contract_address)

        # Get the bytecode with constructor arguments
        source_bytecode = deploy_on_devnet_and_get_bytecode(w3, contract_address)

        # Compare the bytecodes
        if deployed_bytecode == source_bytecode:
            print("✅ Contract verification successful!")
            print("The deployed contract matches the source code.")
            return True

        print("❌ Contract verification failed!")
        print("The deployed contract does not match the source code.")
        return False

    except Exception as e:
        print(f"Error during verification: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Verify Collateral smart contract')
    parser.add_argument('contract_address', help='The address of the deployed contract')
    parser.add_argument('expected_trustee', help='Expected trustee address to verify')
    parser.add_argument('expected_netuid', type=int, help='Expected netuid to verify')
    
    args = parser.parse_args()

    if not Web3.is_address(args.contract_address):
        print("Error: Invalid contract address")
        sys.exit(1)

    assert(verify_contract(args.contract_address, args.expected_trustee, args.expected_netuid))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
