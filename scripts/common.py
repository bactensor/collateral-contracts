import os
import sys
import json
from web3 import Web3
from eth_account import Account


def load_contract_abi():
    """Load the contract ABI from the artifacts file."""
    try:
        with open('../out/Collateral.sol/Collateral.json', 'r') as f:
            contract_json = json.load(f)
            return contract_json['abi']
    except FileNotFoundError:
        print("Error: Contract ABI not found. Please run 'forge build' first.", file=sys.stderr)
        sys.exit(1)


def get_web3_connection():
    """Get Web3 connection from RPC_URL environment variable."""
    rpc_url = os.getenv('RPC_URL')
    if not rpc_url:
        print("Error: RPC_URL environment variable is not set", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("Error: Failed to connect to the network", file=sys.stderr)
        sys.exit(1)
    return w3


def get_account():
    """Get account from DEPOSITOR_PRIVATE_KEY environment variable."""
    private_key = os.getenv('DEPOSITOR_PRIVATE_KEY')
    if not private_key:
        print("Error: DEPOSITOR_PRIVATE_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return Account.from_key(private_key)


def validate_address_format(address):
    """Validate if the given address is a valid Ethereum address."""
    if not Web3.is_address(address):
        print("Error: Invalid contract address", file=sys.stderr)
        sys.exit(1)


def build_and_send_transaction(w3, contract, function_call, account, gas_limit=100000, value=0):
    """Build, sign and send a transaction.
    
    Args:
        w3: Web3 instance
        contract: Contract instance
        function_call: Contract function call to execute
        account: Account to send transaction from
        gas_limit: Maximum gas to use for the transaction
        value: Amount of ETH to send with the transaction (in Wei)
    """
    transaction = function_call.build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': gas_limit,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id,
        'value': value
    })

    signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction sent: {tx_hash.hex()}", file=sys.stderr)
    return tx_hash


def wait_for_receipt(w3, tx_hash):
    """Wait for transaction receipt and return it."""
    return w3.eth.wait_for_transaction_receipt(tx_hash)
