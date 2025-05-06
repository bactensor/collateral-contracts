#!/usr/bin/env python3
import argparse
import sys
from address_conversion import h160_to_ss58


def main():
    parser = argparse.ArgumentParser(description="Get the SS58 address for a given H160 address")
    parser.add_argument("address", help="The address to convert")
    args = parser.parse_args()

    try:
        print(h160_to_ss58(args.address))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
