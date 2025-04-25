#!/usr/bin/env python3

import sys
from address_conversion import h160_to_ss58

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python h160_to_ss58.py <h160_address>")
        sys.exit(1)

    try:
        print(h160_to_ss58(sys.argv[1]))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
