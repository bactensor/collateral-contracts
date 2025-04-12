#!/usr/bin/env python3
import sys
from web3 import Web3
from common import get_web3_connection, get_account, wait_for_receipt
from address_conversion import ss58_to_h160


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python send_eth_to_ss58.py <ss58_address> <amount_in_eth>",
            file=sys.stderr,
        )
        sys.exit(1)

    ss58_address = sys.argv[1]
    try:
        amount_eth = float(sys.argv[2])
    except ValueError:
        print("Error: Amount must be a valid number", file=sys.stderr)
        sys.exit(1)

    h160_address = ss58_to_h160(ss58_address)
    print(
        f"Converting SS58 address {ss58_address} to H160: {h160_address}",
        file=sys.stderr,
    )

    w3 = get_web3_connection()
    account = get_account()

    amount_wei = w3.to_wei(amount_eth, "ether")
    transaction = {
        "from": account.address,
        "to": Web3.to_checksum_address(h160_address),
        "value": amount_wei,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 21000,  # Standard gas limit for ETH transfers
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id,
    }

    signed_txn = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction sent: {tx_hash.hex()}", file=sys.stderr)

    receipt = wait_for_receipt(w3, tx_hash)
    print(f"Transaction successful! Hash: {tx_hash.hex()}", file=sys.stderr)
    print(f"Gas used: {receipt['gasUsed']}", file=sys.stderr)


if __name__ == "__main__":
    main()
