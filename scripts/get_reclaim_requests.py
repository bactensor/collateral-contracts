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


def get_reclaim_process_started_events(w3, contract_address, block_num_low, block_num_high):
    """Fetch all ReclaimProcessStarted events emitted by the Collateral contract within a block range.
    
    Args:
        w3 (Web3): Web3 instance to use for blockchain interaction
        contract_address (str): The address of the deployed Collateral contract
        block_num_low (int): The starting block number (inclusive)
        block_num_high (int): The ending block number (inclusive)
        
    Returns:
        list[ReclaimProcessStartedEvent]: List of ReclaimProcessStarted events
    """
    ABI = [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "reclaimRequestId", "type": "uint256"},
                {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
                {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
                {"indexed": False, "internalType": "uint64", "name": "expirationTime", "type": "uint64"},
                {"indexed": False, "internalType": "string", "name": "url", "type": "string"},
                {"indexed": False, "internalType": "bytes16", "name": "urlContentMd5Checksum", "type": "bytes16"}
            ],
            "name": "ReclaimProcessStarted",
            "type": "event"
        }
    ]

    contract = w3.eth.contract(address=contract_address, abi=ABI)
    
    event_filter = contract.events.ReclaimProcessStarted.create_filter(
        fromBlock=block_num_low,
        toBlock=block_num_high
    )
    
    events = event_filter.get_all_entries()
    
    formatted_events = []
    for event in events:
        formatted_events.append(ReclaimProcessStartedEvent(
            reclaim_request_id=event['args']['reclaimRequestId'],
            account=event['args']['account'],
            amount=event['args']['amount'],
            expiration_time=event['args']['expirationTime'],
            url=event['args']['url'],
            url_content_md5_checksum=event['args']['urlContentMd5Checksum'].hex(),
            block_number=event['blockNumber'],
            transaction_hash=event['transactionHash'].hex(),
        ))
    
    return formatted_events


def main():
    parser = argparse.ArgumentParser(description='Fetch ReclaimProcessStarted events from Collateral contract')
    parser.add_argument('contract_address', help='Address of the deployed Collateral contract')
    parser.add_argument('block_start', type=int, help='Starting block number (inclusive)')
    parser.add_argument('block_end', type=int, help='Ending block number (inclusive)')
    
    args = parser.parse_args()
    
    w3 = get_web3_connection()
    events = get_reclaim_process_started_events(w3, args.contract_address, args.block_start, args.block_end)
    
    fieldnames = [
        'reclaim_request_id',
        'account',
        'amount',
        'expiration_time',
        'url',
        'url_content_md5_checksum',
        'block_number',
        'transaction_hash'
    ]
    
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    
    for event in events:
        writer.writerow({
            'reclaim_request_id': event.reclaim_request_id,
            'account': event.account,
            'amount': event.amount,
            'expiration_time': event.expiration_time,
            'url': event.url,
            'url_content_md5_checksum': event.url_content_md5_checksum,
            'block_number': event.block_number,
            'transaction_hash': event.transaction_hash
        })


if __name__ == '__main__':
    main()
