import argparse
import csv
import sys
from collections import defaultdict
from common import get_web3_connection, get_deposit_events, get_miner_collateral


def main():
    parser = argparse.ArgumentParser(
        description="Get collaterals for miners who deposited in a given block range"
    )
    parser.add_argument(
        "contract_address", help="The address of the deployed Collateral contract"
    )
    parser.add_argument(
        "block_start", type=int, help="Starting block number (inclusive)"
    )
    parser.add_argument(
        "block_end",
        type=int,
        help="Ending block number (inclusive)")
    args = parser.parse_args()

    w3 = get_web3_connection()

    deposit_events = get_deposit_events(
        w3, args.contract_address, args.block_start, args.block_end
    )

    cumulative_deposits = defaultdict(int)
    for event in deposit_events:
        cumulative_deposits[event.account] += event.amount

    miner_addresses = set(event.account for event in deposit_events)
    results = []
    for miner_address in miner_addresses:
        collateral = get_miner_collateral(
            w3, args.contract_address, miner_address)
        results.append(
            [miner_address, cumulative_deposits[miner_address], collateral])

    writer = csv.writer(sys.stdout)
    writer.writerow(
        ["miner_address", "cumulative_amount_of_deposits", "total_collateral_amount"]
    )
    writer.writerows(results)

    print(f"Found {len(results)} miners with deposits", file=sys.stderr)


if __name__ == "__main__":
    main()
