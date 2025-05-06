import argparse
import json
import pathlib
import subprocess
import sys

import bittensor
import bittensor.utils
import bittensor_wallet
from address_conversion import h160_to_ss58
from generate_keypair import generate_and_save_keypair
from subtensor import associate_evm_key

DENY_TIMEOUT = 3 * 24 * 60 * 60  # 3 days
MIN_COLLATERAL_INCREASE = 10000000000000  # 0.01 TAO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "amount_tao",
        help="Amount of TAO to transfer to the EVM wallet",
        type=float,
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy the Contract to the Network",
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
        "--overwrite",
        action="store_true",
        help="Overwrite the existing H160 file with the new one.",
    )
    parser.add_argument(
        "--wallet-hotkey",
        default="default",
        help="Hotkey of the Wallet",
    )
    parser.add_argument(
        "--wallet-name",
        default="default",
        help="Name of the Wallet.",
    )
    parser.add_argument(
        "--wallet-path",
        help="Path where the Wallets are located.",
    )

    args = parser.parse_args()

    wallet = bittensor_wallet.Wallet(
        name=args.wallet_name,
        hotkey=args.wallet_hotkey,
        path=args.wallet_path,
    )
    _, network_url = bittensor.utils.determine_chain_endpoint_and_network(
        args.network,
    )

    try:
        keypair = generate_and_save_keypair(
            output_path=(
                pathlib.Path(wallet.path)
                .expanduser()
                .joinpath(
                    wallet.name,
                    "h160",
                    wallet.hotkey_str,
                )
            ),
            overwrite=args.overwrite,
        )
    except FileExistsError as e:
        print(f"File {e.filename} already exists. Use --overwrite", file=sys.stderr)
        sys.exit(1)

    with bittensor.Subtensor(
        network=network_url,
    ) as subtensor:
        success, error = associate_evm_key(
            subtensor,
            wallet,
            keypair["address"],
            keypair["private_key"],
            args.netuid,
        )

        if not success:
            print(f"Unable to Associate EVM Key. {error}", file=sys.stderr)
            sys.exit(1)

        success = subtensor.transfer(
            wallet,
            dest=h160_to_ss58(keypair["address"]),
            amount=bittensor.Balance.from_tao(args.amount_tao),
            wait_for_inclusion=True,
            wait_for_finalization=True,
        )

        if not success:
            sys.exit(1)

        if not args.deploy:
            return

        try:
            contract = subprocess.run(
                [
                    "./deploy.sh",
                    str(args.netuid),
                    keypair["address"],
                    str(MIN_COLLATERAL_INCREASE),
                    str(DENY_TIMEOUT),
                ],
                capture_output=True,
                check=True,
                cwd=pathlib.Path(__file__).parents[1],
                env={
                    "RPC_URL": network_url,
                    "DEPLOYER_PRIVATE_KEY": keypair["private_key"],
                },
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Unable to Deploy Contract. {e.stderr}", file=sys.stderr)
            sys.exit(2)
        else:
            contract_address = next(
                line.removeprefix("Deployed to: ")
                for line in contract.stdout.split("\n")
                if line.startswith("Deployed to: ")
            )

        try:
            subtensor.commit(
                wallet,
                netuid=args.netuid,
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

        print(f"Published Contract Address: {contract_address}")


if __name__ == "__main__":
    main()
