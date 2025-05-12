import argparse
import json
import pathlib
import sys

import bittensor

from subtensor import associate_evm_key


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wallet-name", required=True)
    parser.add_argument("--wallet-hotkey", required=True)
    parser.add_argument("--wallet-path")
    parser.add_argument("--network", default="finney")
    parser.add_argument("--netuid", type=int, default=12)
    args = parser.parse_args()

    wallet = bittensor.Wallet(
        name=args.wallet_name,
        hotkey=args.wallet_hotkey,
        path=args.wallet_path,
    )

    keyfile = (
        pathlib.Path(wallet.path)
        .expanduser()
        .joinpath(wallet.name, "h160", wallet.hotkey_str)
        .resolve()
    )
    evm_private_key = json.loads(keyfile.read_text())["private_key"]

    with bittensor.subtensor(network=args.network) as subtensor:
        success, error = associate_evm_key(subtensor, wallet, evm_private_key, args.netuid)

    if not success:
        print(f"Unable to Associate EVM Key. {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
