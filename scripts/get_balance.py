import argparse

from web3 import Web3
import bittensor.utils


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    parser.add_argument("--network", default="finney")
    args = parser.parse_args()

    _, network_url = bittensor.utils.determine_chain_endpoint_and_network(
        args.network,
    )

    w3 = Web3(Web3.LegacyWebSocketProvider(network_url))
    balance = w3.eth.get_balance(args.address)

    print("Account Balance:", w3.from_wei(balance, "ether"))
    print("Account Balance (wei):", balance)


if __name__ == "__main__":
    main()
