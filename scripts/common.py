import os
import sys
import json
import hashlib
import requests
from dataclasses import dataclass
from web3 import Web3
from eth_account import Account


def load_contract_abi():
    """Load the contract ABI from the artifacts file."""
    try:
        with open("../out/Collateral.sol/Collateral.json", "r") as f:
            contract_json = json.load(f)
            return contract_json["abi"]
    except FileNotFoundError:
        print(
            "Error: Contract ABI not found. Please run 'forge build' first.",
            file=sys.stderr,
        )
        sys.exit(1)


def get_web3_connection():
    """Get Web3 connection from RPC_URL environment variable."""
    rpc_url = os.getenv("RPC_URL")
    if not rpc_url:
        print("Error: RPC_URL environment variable is not set", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("Error: Failed to connect to the network", file=sys.stderr)
        sys.exit(1)
    return w3


def get_account():
    """Get account from PRIVATE_KEY environment variable."""
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("Error: PRIVATE_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return Account.from_key(private_key)


def get_contract_config(w3, contract_address):
    """
    Get the configuration parameters from a deployed Collateral contract.

    Args:
        w3 (Web3): Web3 instance to use for blockchain interaction
        contract_address (str): The address of the deployed Collateral contract

    Returns:
        tuple: (trustee, decision_timeout, min_collateral_increase, netuid)
    """
    # Contract ABI (minimal ABI for the functions we need)
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


def validate_address_format(address):
    """Validate if the given address is a valid Ethereum address."""
    if not Web3.is_address(address):
        print("Error: Invalid address", file=sys.stderr)
        sys.exit(1)


def build_and_send_transaction(
    w3, contract, function_call, account, gas_limit=100000, value=0
):
    """Build, sign and send a transaction.

    Args:
        w3: Web3 instance
        contract: Contract instance
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
    print(f"Signed transaction: {signed_txn}", file=sys.stderr)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}", file=sys.stderr)
    return tx_hash


def wait_for_receipt(w3, tx_hash):
    """Wait for transaction receipt and return it."""
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def calculate_md5_checksum(url):
    """Calculate MD5 checksum of the content at the given URL.

    Args:
        url (str): The URL to fetch content from.

    Returns:
        str: The MD5 checksum of the content.

    Raises:
        SystemExit: If there's an error fetching the URL content.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return hashlib.md5(response.content).hexdigest()
    except requests.RequestException as e:
        print(f"Error fetching URL content: {str(e)}", file=sys.stderr)
        sys.exit(1)


@dataclass
class DepositEvent:
    """Represents a Deposit event emitted by the Collateral contract."""

    account: str
    amount: int
    block_number: int
    transaction_hash: str


def get_deposit_events(w3, contract_address, block_num_low, block_num_high):
    """Fetch all Deposit events emitted by the Collateral contract within a block range.

    Args:
        w3 (Web3): Web3 instance to use for blockchain interaction
        contract_address (str): The address of the deployed Collateral contract
        block_num_low (int): The starting block number (inclusive)
        block_num_high (int): The ending block number (inclusive)

    Returns:
        list[DepositEvent]: List of Deposit events
    """
    # Create the event signature hash for the Deposit event using Web3.py's built-in functionality
    event_signature = "Deposit(address,uint256)"
    event_topic = w3.keccak(text=event_signature).hex()

    # Convert contract address to checksum format
    checksum_address = w3.to_checksum_address(contract_address)

    # Prepare the filter parameters for eth_getLogs
    filter_params = {
        "fromBlock": hex(block_num_low),
        "toBlock": hex(block_num_high),
        "address": checksum_address,
        "topics": [event_topic]
    }

    # Get the logs using eth_getLogs
    logs = w3.eth.get_logs(filter_params)

    formatted_events = []
    for log in logs:
        # The first topic is the event signature, second is the indexed account address
        # Convert the account address to checksum format
        account_address = "0x" + log["topics"][1].hex()[-40:]
        account = w3.to_checksum_address(account_address)
        
        # The data field contains the non-indexed amount parameter as bytes
        amount = int.from_bytes(log["data"], byteorder='big')
        
        formatted_events.append(
            DepositEvent(
                account=account,
                amount=amount,
                block_number=log["blockNumber"],
                transaction_hash=log["transactionHash"].hex(),
            )
        )

    return formatted_events


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

    try:
        return contract.functions.collaterals(miner_address).call()
    except Exception as e:
        print(f"Error querying collateral: {str(e)}", file=sys.stderr)
        sys.exit(1)
