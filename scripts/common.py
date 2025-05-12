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

import bittensor
import requests
import web3.providers.auto
from eth_typing import URI
from web3 import Web3
from eth_account import Account
from web3.exceptions import ContractLogicError


def load_contract_abi():
    """Load the contract ABI from the artifacts file."""
    abi_file = pathlib.Path(__file__).parent.parent / "abi.json"
    return json.loads(abi_file.read_text())


RPC_URLS = {
    "finney": "https://lite.chain.opentensor.ai",
    "test": "https://test.chain.opentensor.ai",
}


def get_web3_connection(network: str) -> Web3:
    """Get Web3 connection for the specified network."""
    if network in RPC_URLS:
        network_url = RPC_URLS[network]
    else:
        _, network_url = bittensor.utils.determine_chain_endpoint_and_network(network)
    w3 = Web3(web3.providers.auto.load_provider_from_uri(URI(network_url)))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the network")
    return w3


def get_account(keyfile=None):
    """Get the account from the keyfile or PRIVATE_KEY environment variable."""
    if keyfile:
        account_data = json.loads(pathlib.Path(keyfile).expanduser().read_text())
        private_key = account_data.get("private_key")
    else:
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


def get_revert_reason(w3, tx_hash, block_number):
    """Returns the custom Solidity error name for a failed transaction, or 'Could not parse error' if not decodable."""
    tx = w3.eth.get_transaction(tx_hash)
    try:
        w3.eth.call({
            'to': tx['to'],
            'from': tx['from'],
            'data': tx['input'],
            'value': tx['value'],
        }, block_identifier=block_number)
    except ContractLogicError as e:
        import re
        msg = str(e)
        hex_pattern = re.compile(r'(0x[a-fA-F0-9]{8,})')
        match = hex_pattern.search(msg)
        revert_data = match.group(1) if match else None
        if revert_data and len(revert_data) >= 10:
            selector = revert_data[:10]
            contract_abi = load_contract_abi()
            for item in contract_abi:
                if item.get('type') == 'error':
                    sig = item['name'] + '(' + ','.join([input['type'] for input in item.get('inputs', [])]) + ')'
                    import eth_utils
                    selector_bytes = eth_utils.keccak(text=sig)[:4]
                    selector_hex = '0x' + selector_bytes.hex()
                    if selector == selector_hex:
                        return item['name']
        return "Could not parse error"
    return "Could not parse error"


def get_evm_key_associations(
    subtensor: bittensor.Subtensor, netuid: int, block: int | None = None
) -> dict[int, str]:
    """
    Retrieve all EVM key associations for a specific subnet.

    Arguments:
        subtensor (bittensor.Subtensor): The Subtensor object to use for querying the network.
        netuid (int): The NetUID for which to retrieve EVM key associations.
        block (int | None, optional): The block number to query. Defaults to None, which queries the latest block.

    Returns:
        dict: A dictionary mapping UIDs (int) to their associated EVM key addresses (str).
    """
    associations = subtensor.query_map_subtensor(
        "AssociatedEvmAddress", block=block, params=[netuid]
    )
    uid_evm_address_map = {}
    for uid, scale_obj in associations:
        evm_address_raw, block = scale_obj.value
        evm_address = "0x" + bytes(evm_address_raw[0]).hex()
        uid_evm_address_map[uid] = evm_address
    return uid_evm_address_map
