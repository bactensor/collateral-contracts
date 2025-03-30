#!/usr/bin/env python3

import subprocess
import sys
import time
from web3 import Web3
from common import get_web3_connection, get_contract_config

# Constants
ANVIL_PORT = 8555
ANVIL_RPC_URL = f"http://127.0.0.1:{ANVIL_PORT}"
# the first preset private key available in anvil
ANVIL_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def get_deployed_bytecode(w3, contract_address):
    """Get the deployed contract's bytecode."""
    return w3.eth.get_code(contract_address).hex()


def deploy_on_devnet_and_get_bytecode(w3, contract_address):
    """Deploy the contract on anvil and return its bytecode."""
    # Get constructor arguments from the deployed contract
    netuid, trustee, decision_timeout, min_collateral_increase = get_contract_config(
        w3, contract_address
    )

    # Start anvil in the background
    anvil_process = subprocess.Popen(
        ["anvil", "--port", str(ANVIL_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for anvil to start
        time.sleep(2)

        # Deploy the contract using forge create
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

        # Extract the deployed address
        deployed_address = (
            deploy_output.stdout.split("Deployed to: ")[1].strip().split()[0]
        )
        # Get the bytecode of the deployed contract
        devnet_w3 = Web3(Web3.HTTPProvider(ANVIL_RPC_URL))
        return get_deployed_bytecode(devnet_w3, deployed_address)

    finally:
        # Clean up anvil process
        anvil_process.terminate()
        anvil_process.wait()


def verify_contract(contract_address):
    """Verify if the deployed contract matches the source code."""
    try:
        # Connect to the blockchain
        w3 = get_web3_connection()

        deployed_bytecode = get_deployed_bytecode(w3, contract_address)

        # Get the bytecode with constructor arguments
        source_bytecode = deploy_on_devnet_and_get_bytecode(w3, contract_address)

        # Compare the bytecodes
        if deployed_bytecode == source_bytecode:
            print("✅ Contract verification successful!")
            print("The deployed contract matches the source code.")
            return True
        else:
            print("❌ Contract verification failed!")
            print("The deployed contract does not match the source code.")
            return False

    except Exception as e:
        print(f"Error during verification: {str(e)}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python verify_contract.py <contract_address>")
        print("Example: python verify_contract.py 0x123...abc")
        print("Note: Set RPC_URL environment variable for the blockchain endpoint")
        sys.exit(1)

    contract_address = sys.argv[1]

    if not Web3.is_address(contract_address):
        print("Error: Invalid contract address")
        sys.exit(1)

    verify_contract(contract_address)


if __name__ == "__main__":
    main()
