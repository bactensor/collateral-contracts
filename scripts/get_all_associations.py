import argparse
import sys

import bittensor

from common import get_evm_key_associations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--netuid", type=int, required=True)
    parser.add_argument("--block", type=int, default=None)
    parser.add_argument("--network", default="finney")
    args = parser.parse_args()

    with bittensor.subtensor(network=args.network) as subtensor:
        metagraph = subtensor.metagraph(netuid=args.netuid, block=args.block)
        associations = get_evm_key_associations(subtensor, args.netuid, args.block)

        if not associations:
            print(f"No associations found for netuid {args.netuid}", file=sys.stderr)
            sys.exit(1)

        uid_to_hotkey_map = {neuron.uid: neuron.hotkey for neuron in metagraph.neurons}

        print(f"EVM key associations for netuid {args.netuid}:\n")
        print(" UID | Hotkey                                           | EVM Address")
        print("-----|--------------------------------------------------|-------------------------------------------")
        for uid in sorted(associations.keys()):
            hotkey = uid_to_hotkey_map.get(uid, "Unknown")
            evm_address = associations[uid]
            print(f"{uid:4} | {hotkey:48} | {evm_address}")


if __name__ == "__main__":
    main()
