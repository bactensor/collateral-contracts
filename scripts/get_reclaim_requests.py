#!/usr/bin/env python3

import sys
import csv
import argparse
from dataclasses import dataclass
from common import get_web3_connection


@dataclass
class ReclaimProcessStartedEvent:
    """Represents a ReclaimProcessStarted event emitted by the Collateral contract."""

    reclaim_request_id: int
    account: str
    amount: int
    expiration_time: int
    url: str
    url_content_md5_checksum: str
    block_number: int
    transaction_hash: str


def get_reclaim_process_started_events(
    w3, contract_address, block_num_low, block_num_high
):
    """Fetch all ReclaimProcessStarted events emitted by the Collateral contract within a block range.

    Args:
        w3 (Web3): Web3 instance to use for blockchain interaction
        contract_address (str): The address of the deployed Collateral contract
        block_num_low (int): The starting block number (inclusive)
        block_num_high (int): The ending block number (inclusive)

    Returns:
        list[ReclaimProcessStartedEvent]: List of ReclaimProcessStarted events
    """
    # Event signature for ReclaimProcessStarted
    event_signature = "ReclaimProcessStarted(uint256,address,uint256,uint64,string,bytes16)"
    event_topic = w3.keccak(text=event_signature).hex()

    # Create filter parameters for eth_getLogs
    filter_params = {
        "fromBlock": hex(block_num_low),
        "toBlock": hex(block_num_high),
        "address": contract_address,
        "topics": [
            event_topic,  # Event signature topic
            None,  # reclaimRequestId (indexed)
            None,  # account (indexed)
        ]
    }

    # Get logs using eth_getLogs
    logs = w3.eth.get_logs(filter_params)

    formatted_events = []
    for log in logs:
        # Decode the non-indexed parameters from the data field
        data = log['data']
        # Remove '0x' prefix and split into 64-character chunks (32 bytes each)
        data_chunks = [data[2:][i:i+64] for i in range(0, len(data[2:]), 64)]
        
        # Decode the parameters
        amount = int(data_chunks[0], 16)
        expiration_time = int(data_chunks[1], 16)
        # URL and checksum are dynamic length, need to be decoded differently
        # This is a simplified version - in production you'd want proper ABI decoding
        url_length = int(data_chunks[2], 16)
        url = bytes.fromhex(data_chunks[3][:url_length*2]).decode('utf-8')
        url_content_md5_checksum = data_chunks[4]

        formatted_events.append(
            ReclaimProcessStartedEvent(
                reclaim_request_id=int(log['topics'][1].hex(), 16),  # First indexed parameter
                account=log['topics'][2],  # Second indexed parameter
                amount=amount,
                expiration_time=expiration_time,
                url=url,
                url_content_md5_checksum=url_content_md5_checksum,
                block_number=log['blockNumber'],
                transaction_hash=log['transactionHash'].hex(),
            )
        )

    return formatted_events


def main():
    parser = argparse.ArgumentParser(
        description="Fetch ReclaimProcessStarted events from Collateral contract"
    )
    parser.add_argument(
        "contract_address", help="Address of the deployed Collateral contract"
    )
    parser.add_argument(
        "block_start", type=int, help="Starting block number (inclusive)"
    )
    parser.add_argument("block_end", type=int, help="Ending block number (inclusive)")

    args = parser.parse_args()

    w3 = get_web3_connection()
    events = get_reclaim_process_started_events(
        w3, args.contract_address, args.block_start, args.block_end
    )

    fieldnames = [
        "reclaim_request_id",
        "account",
        "amount",
        "expiration_time",
        "url",
        "url_content_md5_checksum",
        "block_number",
        "transaction_hash",
    ]

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()

    for event in events:
        writer.writerow(
            {
                "reclaim_request_id": event.reclaim_request_id,
                "account": event.account,
                "amount": event.amount,
                "expiration_time": event.expiration_time,
                "url": event.url,
                "url_content_md5_checksum": event.url_content_md5_checksum,
                "block_number": event.block_number,
                "transaction_hash": event.transaction_hash,
            }
        )


if __name__ == "__main__":
    main()
