#!/usr/bin/env python3

"""
Collateral Deposit Script

This script allows users to deposit collateral into the Collateral smart contract.
It handles validation of minimum collateral amounts, trustee verification, and
executes the deposit transaction on the blockchain.
"""

import sys
from web3 import Web3
from common import (
    load_contract_abi,
    get_web3_connection,
    get_account,
    validate_address_format,
    build_and_send_transaction,
    wait_for_receipt,
)


def check_minimum_collateral(contract, amount_wei):
    """Check if the amount meets minimum collateral requirement."""
    min_collateral = contract.functions.MIN_COLLATERAL_INCREASE().call()
    if amount_wei < min_collateral:
        print(
            f"Error: Amount {Web3.from_wei(amount_wei, 'ether')} TAO is less than "
            f"minimum required {Web3.from_wei(min_collateral, 'ether')} TAO",
            file=sys.stderr,
        )
        sys.exit(1)
    return min_collateral


def verify_trustee(contract, expected_trustee):
    """Verify if the provided trustee address matches the contract's trustee."""
    trustee = contract.functions.TRUSTEE().call()
    if trustee.lower() != expected_trustee.lower():
        print(
            f"Error: Trustee address mismatch. Expected: {expected_trustee}, "
            f"Got: {trustee}",
            file=sys.stderr,
        )
        sys.exit(1)


def deposit_collateral(w3, account, amount_tao,
                       contract_address, trustee_address):
    """Deposit collateral into the contract.

    Args:
        w3: Web3 instance
        account: Account to use for the transaction
        amount_tao: Amount to deposit in TAO
        contract_address: Address of the contract
        trustee_address: Optional trustee address to verify

    Returns:
        tuple: (deposit_event, receipt)
    """
    validate_address_format(contract_address)
    validate_address_format(trustee_address)

    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    verify_trustee(contract, trustee_address)

    amount_wei = w3.to_wei(amount_tao, "ether")

    try:
        check_minimum_collateral(contract, amount_wei)

        tx_hash = build_and_send_transaction(
            w3, contract.functions.deposit(), account, value=amount_wei
        )

        receipt = wait_for_receipt(w3, tx_hash)
        deposit_event = contract.events.Deposit().process_receipt(receipt)[0]

        return deposit_event, receipt

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Handle command line arguments and execute deposit."""
    if len(sys.argv) != 4:
        print(
            "Usage: ./deposit_collateral.py <contract_address> "
            "<amount_in_tao> <trustee_address>",
            file=sys.stderr,
        )
        print(
            "Example: python deposit_collateral.py 0x123... 1.5 0x456...",
            file=sys.stderr,
        )
        sys.exit(1)

    contract_address = sys.argv[1]
    amount_tao = float(sys.argv[2])
    trustee_address = sys.argv[3]

    w3 = get_web3_connection()
    account = get_account()

    deposit_event, receipt = deposit_collateral(
        w3=w3,
        account=account,
        amount_tao=amount_tao,
        contract_address=contract_address,
        trustee_address=trustee_address,
    )

    print(f"Successfully deposited {amount_tao} TAO")
    print("Event details:")
    print(f"  Account: {deposit_event['args']['account']}")
    print(
        f"  Amount: {w3.from_wei(deposit_event['args']['amount'], 'ether')} TAO")
    print(f"  Transaction hash: {receipt['transactionHash'].hex()}")
    print(f"  Block number: {receipt['blockNumber']}")


if __name__ == "__main__":
    main()
