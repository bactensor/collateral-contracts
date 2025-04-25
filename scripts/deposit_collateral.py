#!/usr/bin/env python3

"""
Collateral Deposit Script

This script allows users to deposit collateral into the Collateral smart contract.
It handles validation of minimum collateral amounts, trustee verification, and
executes the deposit transaction on the blockchain.
"""

import sys
import argparse
from web3 import Web3
from common import (
    load_contract_abi,
    get_web3_connection,
    get_account,
    validate_address_format,
    build_and_send_transaction,
    wait_for_receipt,
)


class DepositCollateralError(Exception):
    """Custom exception for collateral deposit related errors."""
    pass


def check_minimum_collateral(contract, amount_wei):
    """Check if the amount meets minimum collateral requirement."""
    min_collateral = contract.functions.MIN_COLLATERAL_INCREASE().call()
    if amount_wei < min_collateral:
        raise ValueError(
            f"Error: Amount {Web3.from_wei(amount_wei, 'ether')} TAO is less than "
            f"minimum required {Web3.from_wei(min_collateral, 'ether')} TAO"
        )
    return min_collateral


def verify_trustee(contract, expected_trustee):
    """Verify if the provided trustee address matches the contract's trustee."""
    trustee = contract.functions.TRUSTEE().call()
    if trustee.lower() != expected_trustee.lower():
        raise ValueError(
            f"Error: Trustee address mismatch. Expected: {expected_trustee}, "
            f"Got: {trustee}"
        )


def deposit_collateral(w3, account, amount_tao,
                       contract_address, trustee_address):
    """Deposit collateral into the contract.

    Args:
        w3: Web3 instance
        account: Account to use for the transaction
        amount_tao: Amount to deposit in TAO
        contract_address: Address of the contract
        trustee_address: Trustee address to verify

    Returns:
        tuple: (deposit_event, receipt)
    """
    validate_address_format(contract_address)
    validate_address_format(trustee_address)

    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    verify_trustee(contract, trustee_address)

    amount_wei = w3.to_wei(amount_tao, "ether")
    check_minimum_collateral(contract, amount_wei)

    tx_hash = build_and_send_transaction(
        w3, contract.functions.deposit(), account, value=amount_wei
    )

    receipt = wait_for_receipt(w3, tx_hash)
    if receipt['status'] == 0:
        raise DepositCollateralError(f"Transaction failed for depositing collateral")
    deposit_event = contract.events.Deposit().process_receipt(receipt)[0]

    return deposit_event, receipt


def main():
    """Handle command line arguments and execute deposit."""
    parser = argparse.ArgumentParser(
        description="Deposit collateral into the Collateral smart contract"
    )
    parser.add_argument(
        "contract_address",
        help="Address of the Collateral contract"
    )
    parser.add_argument(
        "amount_tao",
        type=float,
        help="Amount of TAO to deposit"
    )
    parser.add_argument(
        "trustee_address",
        help="Expected trustee address to verify"
    )

    args = parser.parse_args()

    w3 = get_web3_connection()
    account = get_account()

    deposit_event, receipt = deposit_collateral(
        w3=w3,
        account=account,
        amount_tao=args.amount_tao,
        contract_address=args.contract_address,
        trustee_address=args.trustee_address,
    )

    print(f"Successfully deposited {args.amount_tao} TAO")
    print("Event details:")
    print(f"  Account: {deposit_event['args']['account']}")
    print(
        f"  Amount: {w3.from_wei(deposit_event['args']['amount'], 'ether')} TAO")
    print(f"  Transaction hash: {receipt['transactionHash'].hex()}")
    print(f"  Block number: {receipt['blockNumber']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
