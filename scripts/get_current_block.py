import argparse

import bittensor.utils
from web3 import Web3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", default="finney")
    args = parser.parse_args()

    _, network_url = bittensor.utils.determine_chain_endpoint_and_network(
        args.network,
    )

    w3 = Web3(Web3.LegacyWebSocketProvider(network_url))
    print(w3.eth.get_block('latest')['number'])


if __name__ == "__main__":
    main()
