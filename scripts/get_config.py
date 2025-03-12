from web3 import Web3
import os
import sys
import argparse

def get_web3():
    rpc_url = os.getenv('RPC_URL')
    if not rpc_url:
        print("Error: RPC_URL environment variable is not set")
        sys.exit(1)
    return Web3(Web3.HTTPProvider(rpc_url))

def get_config(w3, contract_address):
    """
    Get the configuration parameters from a deployed Collateral contract.
    
    Args:
        w3 (Web3): Web3 instance to use for blockchain interaction
        contract_address (str): The address of the deployed Collateral contract
        
    Returns:
        tuple: (trustee, decision_timeout, min_collateral_increase)
    """
    # Contract ABI (minimal ABI for the functions we need)
    ABI = [
        {
            "inputs": [],
            "name": "TRUSTEE",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "DECISION_TIMEOUT",
            "outputs": [{"internalType": "uint64", "name": "", "type": "uint64"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "MIN_COLLATERAL_INCREASE",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    # Create contract instance
    contract = w3.eth.contract(address=contract_address, abi=ABI)
    
    # Query the values
    trustee = contract.functions.TRUSTEE().call()
    decision_timeout = contract.functions.DECISION_TIMEOUT().call()
    min_collateral_increase = contract.functions.MIN_COLLATERAL_INCREASE().call()
    
    return trustee, decision_timeout, min_collateral_increase

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Query Collateral contract parameters')
    parser.add_argument('contract_address', help='The address of the deployed Collateral contract')
    args = parser.parse_args()

    # Get Web3 instance
    w3 = get_web3()
    
    # Get configuration
    trustee, decision_timeout, min_collateral_increase = get_config(w3, args.contract_address)
    
    # Print results
    print(f"TRUSTEE: {trustee}")
    print(f"DECISION_TIMEOUT: {decision_timeout} seconds")
    print(f"MIN_COLLATERAL_INCREASE: {min_collateral_increase} wei")

if __name__ == "__main__":
    main() 