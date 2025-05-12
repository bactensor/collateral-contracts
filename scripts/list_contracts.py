import argparse
import asyncio
import json
import pathlib
import sys

import bittensor.utils
import bittensor_wallet
from bittensor import rao
from common import get_miner_collateral, get_web3_connection


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-collateral",
        action="store_true",
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

    try:
        with open(
            pathlib.Path(wallet.path)
            .expanduser()
            .joinpath(
                wallet.name,
                "h160",
                wallet.hotkey_str,
            ),
        ) as keyfile:
            keypair = json.load(keyfile)
    except OSError as e:
        print(f"Unable to open H160 keyfile. {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Unable to decode H160 keyfile. {e}")
        sys.exit(1)

    w3 = get_web3_connection(args.network)

    async with bittensor.AsyncSubtensor(
        network=args.network,
    ) as subtensor:
        block = await subtensor.get_current_block()

        stake_threshold, metagraph, commitments, associations = await asyncio.gather(
            subtensor.query_module(
                "SubtensorModule",
                "StakeThreshold",
                block=block,
            ),
            subtensor.metagraph(
                block=block,
                netuid=args.netuid,
            ),
            subtensor.get_all_commitments(
                block=block,
                netuid=args.netuid,
            ),
            subtensor.query_map_subtensor(
                "AssociatedEvmAddress",
                block=block,
                params=[args.netuid],
            ),
        )

        validators = {
            hotkey: uid
            for uid, hotkey, stake in zip(
                metagraph.uids,
                metagraph.hotkeys,
                metagraph.total_stake,
            )
            if stake >= rao(stake_threshold.value).tao
        }
        associations = {
            uid: bytes(association.value[0][0]).hex()
            async for uid, association in associations
        }

        for hotkey, commitment in commitments.items():
            if hotkey not in validators:
                continue

            try:
                evm_address = associations[validators[hotkey]]
            except KeyError:
                evm_address = "?"

            try:
                contract_address = json.loads(commitment)["contract"]["address"]
            except json.JSONDecodeError:
                continue
            except TypeError:
                continue
            except KeyError:
                continue

            print(f"HotKey {hotkey}")
            print(f"- EVM Address: {evm_address}")
            print(f"- Contract Address: {contract_address}")

            # collateral checking is a blocking function so we make it optional
            if args.check_collateral:
                collateral = get_miner_collateral(
                    w3,
                    contract_address,
                    keypair["address"],
                )

                print(f"- My Collateral: {w3.from_wei(collateral, 'ether')} TAO")


if __name__ == "__main__":
    asyncio.run(main())
