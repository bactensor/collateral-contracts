#!/bin/bash

# Example usage:
#   ./verify-with-taostats.sh <contract address>  
#
# Arguments explanation:
# 1. contract address: Ethereum address of the contract, deployed on mainnet with ./deploy.sh or ./scripts/setup_evm.py (H160 format)
#    Example: 0x902042E72d0BBF72c80c0790564266ae54EBB2bd
#
#

# Check if all required arguments are provided
if [ "$#" -ne 1 ]; then
    echo "Error: Required arguments missing"
    echo "Usage: $0 <contract address>"
    exit 1
fi

# Assign command line arguments to variables
CONTRACT_ADDRESS=$1

# Validate contract address format (0x followed by 40 hex characters)
if ! [[ $CONTRACT_ADDRESS =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "Error: Invalid contract address format. Must be a valid H160 address (0x followed by 40 hex characters)"
    exit 1
fi


forge verify-contract "$CONTRACT_ADDRESS" src/Collateral.sol:Collateral \
    --rpc-url "https://evm.taostats.io/api/eth-rpc" \
    --verifier blockscout \
    --verifier-url "https://evm.taostats.io/api/" \


