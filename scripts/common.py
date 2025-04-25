"""
Common Utilities for Collateral Management

This module provides shared functionality for interacting with the Collateral smart contract.
It includes utilities for:
- Loading contract ABIs
- Establishing Web3 connections
- Managing accounts and transactions
- Retrieving and processing blockchain events
- Validating addresses and calculating checksums
"""

import os
import pathlib
import sys
import json
import hashlib
import requests
from web3 import Web3
from eth_account import Account


def load_contract_abi():
    """Load the contract ABI from the artifacts file."""
    abi_file = pathlib.Path(__file__).parent.parent / "abi.json"
    return json.loads(abi_file.read_text())


def get_web3_connection():
    """Get Web3 connection from RPC_URL environment variable."""
    rpc_url = os.getenv("RPC_URL")
    if not rpc_url:
        raise KeyError("RPC_URL environment variable is not set")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the network")
    return w3


def get_account():
    """Get account from PRIVATE_KEY environment variable."""
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        raise KeyError("PRIVATE_KEY environment variable not set")
    return Account.from_key(private_key)


def validate_address_format(address):
    """Validate if the given address is a valid Ethereum address."""
    if not Web3.is_address(address):
        raise ValueError("Invalid address")


def build_and_send_transaction(
    w3, function_call, account, gas_limit=100000, value=0
):
    """Build, sign and send a transaction.

    Args:
        w3: Web3 instance
        function_call: Contract function call to execute
        account: Account to send transaction from
        gas_limit: Maximum gas to use for the transaction
        value: Amount of ETH to send with the transaction (in Wei)
    """
    transaction = function_call.build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": gas_limit,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
            "value": value,
        }
    )

    signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
    
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}", file=sys.stderr)
    return tx_hash


def wait_for_receipt(w3, tx_hash, timeout=300, poll_latency=2):
    """Wait for transaction receipt and return it."""
    return w3.eth.wait_for_transaction_receipt(tx_hash, timeout, poll_latency)


def calculate_md5_checksum(url):
    """Calculate MD5 checksum of the content at the given URL.

    Args:
        url (str): The URL to fetch content from.

    Returns:
        str: The MD5 checksum of the content.

    Raises:
        SystemExit: If there's an error fetching the URL content.
    """
    response = requests.get(url)
    response.raise_for_status()
    return hashlib.md5(response.content).hexdigest()


def get_miner_collateral(w3, contract_address, miner_address):
    """Query the collateral amount for a given miner address.

    Args:
        w3: Web3 instance
        contract_address: Address of the Collateral contract
        miner_address: Address of the miner to query

    Returns:
        number: Collateral amount in Wei

    Raises:
        SystemExit: If there's an error querying the collateral
    """
    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    return contract.functions.collaterals(miner_address).call()
