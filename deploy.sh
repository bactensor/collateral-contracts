#!/bin/bash

# Example usage:
# First set the required environment variables:
#   export RPC_URL="https://lite.chain.opentensor.ai"
#   export DEPLOYER_PRIVATE_KEY="your-private-key"
#
# Then run the script:
#   ./deploy.sh 0x742d35Cc6634C0532925a3b844Bc454e4438f44e 1000000000000000000 3600
#
# Arguments explanation:
# 1. trustee_h160_address: Ethereum address of the trustee (H160 format)
#    Example: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
#
# 2. min_collateral_increase_u256: Minimum amount for deposits/reclaims in wei
#    Example: 1000000000000000000 (= 1 TAO in wei)
#
# 3. deny_timeout_u64: Time window in seconds for trustee to deny reclaim requests
#    Example: 3600 (= 1 hour in seconds)
#

# Check if all required arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Error: Required arguments missing"
    echo "Usage: $0 <trustee_h160_address> <min_collateral_increase_u256> <deny_timeout_u64>"
    exit 1
fi

# Assign command line arguments to variables
TRUSTEE_ADDRESS=$1
MIN_COLLATERAL_INCREASE=$2
DENY_TIMEOUT=$3

# Check if environment variables are set
if [ -z "$RPC_URL" ]; then
    echo "Error: RPC_URL environment variable is not set"
    exit 1
fi

if [ -z "$DEPLOYER_PRIVATE_KEY" ]; then
    echo "Error: DEPLOYER_PRIVATE_KEY environment variable is not set"
    exit 1
fi

# Validate trustee address format (0x followed by 40 hex characters)
if ! [[ $TRUSTEE_ADDRESS =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "Error: Invalid trustee address format. Must be a valid H160 address (0x followed by 40 hex characters)"
    exit 1
fi

# Execute the forge create command
forge create src/Collateral.sol:Collateral \
    --broadcast \
    --rpc-url "$RPC_URL" \
    --private-key "$DEPLOYER_PRIVATE_KEY" \
    --constructor-args "$TRUSTEE_ADDRESS" "$MIN_COLLATERAL_INCREASE" "$DENY_TIMEOUT"
    