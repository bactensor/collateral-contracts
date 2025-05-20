import argparse
import asyncio
import json
import sys

import bittensor
from bittensor import rao
from common import get_miner_collateral, get_web3_connection, get_account


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
    parser.add_argument("--keyfile", help="Path to keypair file")

    args = parser.parse_args()

    if args.check_collateral:
        try:
            account = get_account(args.keyfile)
        except KeyError:
            print("You need to pass --keyfile when --check-collateral is present.", file=sys.stderr)
            sys.exit(1)
    else:
        account = None

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
            print(f"- EVM Address: 0x{evm_address}")
            print(f"- Contract Address: {contract_address}")

            # collateral checking is a blocking function so we make it optional
            if args.check_collateral:
                collateral = get_miner_collateral(
                    w3,
                    contract_address,
                    account.address,
                )

                print(f"- My Collateral: {w3.from_wei(collateral, 'ether')} TAO")


if __name__ == "__main__":
    asyncio.run(main())
