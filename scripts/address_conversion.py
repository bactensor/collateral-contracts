#!/usr/bin/env python3
"""
Address Conversion Utilities

This module provides functions for converting between different address formats
used in blockchain systems. It supports conversion between SS58 addresses (used
in Substrate-based chains) and H160 addresses (Ethereum-style addresses).
"""
import hashlib

import bittensor_wallet
import scalecodec


def ss58_to_pubkey(ss58_address: str) -> bytes:
    """
    Convert SS58 address to public key bytes.

    Args:
        ss58_address (str): The SS58 address to convert

    Returns:
        bytes: The 32-byte public key

    Raises:
        ValueError: If the SS58 address is invalid
    """
    try:
        keypair = bittensor_wallet.Keypair(ss58_address=ss58_address)

        return keypair.public_key

    except Exception as e:
        raise ValueError(
            f"Error converting SS58 address to public key: {str(e)}")


# https://github.com/opentensor/evm-bittensor/blob/main/examples/address-mapping.js
def h160_to_ss58(h160_address: str, ss58_format: int = 42) -> str:
    """
    Convert H160 (Ethereum address to SS58 address.

    Args:
        h160_address (str): The H160 address to convert ('0x' prefixed or not)

    Returns:
        str: The ss58 address
    """
    if h160_address.startswith("0x"):
        h160_address = h160_address[2:]

    address_bytes = bytes.fromhex(h160_address)

    prefixed_address = bytes("evm:", "utf-8") + address_bytes

    checksum = hashlib.blake2b(prefixed_address, digest_size=32).digest()

    return scalecodec.ss58_encode(checksum, ss58_format=ss58_format)
