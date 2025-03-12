import argparse
from common import get_web3_connection, get_contract_config


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Query Collateral contract parameters')
    parser.add_argument('contract_address', help='The address of the deployed Collateral contract')
    args = parser.parse_args()

    w3 = get_web3_connection()

    trustee, decision_timeout, min_collateral_increase, netuid = get_contract_config(w3, args.contract_address)

    print(f"SUBNET NETUID: {netuid}")
    print(f"TRUSTEE: {trustee}")
    print(f"DECISION_TIMEOUT: {decision_timeout} seconds")
    print(f"MIN_COLLATERAL_INCREASE: {min_collateral_increase} wei")


if __name__ == "__main__":
    main()
