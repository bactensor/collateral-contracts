import argparse
import json
import sys

import bittensor
import bittensor.utils
import bittensor_wallet

from common import validate_address_format

def publish_contract_address(subtensor, wallet, netuid, contract_address):
    try:
        print("Publishing contract address as knowledge commitment.", flush=True)
        subtensor.commit(
            wallet,
            netuid=netuid,
            data=json.dumps(
                {
                    "contract": {
                        "address": contract_address,
                    },
                }
            ),
        )
    except bittensor.MetadataError as e:
        print(f"Unable to Publish Contract Address. {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract-address", 
        required=True, 
        help="The address of the deployed Collateral contract",
    )
    parser.add_argument(
        "--netuid",
        help="Netuid of the Subnet in the Network.",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--network",
        default="finney",
        help="The Subtensor Network to connect to.",
    )
    parser.add_argument(
        "--wallet-hotkey",
        default="default",
        help="Hotkey of the Wallet",
    )
    parser.add_argument(
        "--wallet-name",
        required=True,
        help="Name of the Wallet.",
    )
    parser.add_argument(
        "--wallet-path",
        help="Path where the Wallets are located.",
    )

    args = parser.parse_args()

    validate_address_format(args.contract_address)

    wallet = bittensor_wallet.Wallet(
        name=args.wallet_name,
        hotkey=args.wallet_hotkey,
        path=args.wallet_path,
    )
    _, network_url = bittensor.utils.determine_chain_endpoint_and_network(
        args.network,
    )

    with bittensor.Subtensor(
        network=network_url,
    ) as subtensor:

        publish_contract_address(subtensor, wallet, args.netuid, args.contract_address)


if __name__ == "__main__":
    main()
