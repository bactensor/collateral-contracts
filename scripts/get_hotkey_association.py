import argparse
import sys

import bittensor

from common import get_evm_key_associations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--netuid", type=int, required=True)
    parser.add_argument("--hotkey", required=True)
    parser.add_argument("--block", type=int, default=None)
    parser.add_argument("--network", default="finney")
    args = parser.parse_args()

    with bittensor.subtensor(network=args.network) as subtensor:
        # get the uid of the given hotkey from the metagraph
        metagraph = subtensor.metagraph(netuid=args.netuid, block=args.block)
        neurons = [neuron for neuron in metagraph.neurons if neuron.hotkey == args.hotkey]
        if not neurons:
            print(f"No neuron found for hotkey {args.hotkey} on netuid {args.netuid}", file=sys.stderr)
            sys.exit(1)
        uid = neurons[0].uid

        associations = get_evm_key_associations(subtensor, args.netuid, args.block)
        if uid not in associations:
            print(f"No association found for hotkey {args.hotkey} on netuid {args.netuid}", file=sys.stderr)
            sys.exit(1)

        print(f"EVM key address for neuron {args.hotkey}(uid={uid}) on netuid {args.netuid}: {associations[uid]}")


if __name__ == "__main__":
    main()
