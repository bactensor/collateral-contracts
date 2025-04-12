#!/usr/bin/env python3
from substrateinterface import Keypair
from substrateinterface.utils.ss58 import ss58_encode
import hashlib
import base58

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
        # Create a Keypair from the SS58 address
        keypair = Keypair(ss58_address=ss58_address)

        # Get the public key (32 bytes)
        return keypair.public_key

    except Exception as e:
        raise ValueError(f"Error converting SS58 address to public key: {str(e)}")


# https://github.com/opentensor/evm-bittensor/blob/main/examples/address-mapping.js
def h160_to_ss58(h160_address: str, ss58_format: int = 42) -> str:
    """
    Convert H160 (Ethereum address to SS58 address.

    Args:
        h160_address (str): The H160 address to convert ('0x' prefixed or not)

    Returns:
        str: The ss58 address
    """
    # Ensure the address is in bytes
    if h160_address.startswith("0x"):
        h160_address = h160_address[2:]

    # Convert hex string to bytes
    address_bytes = bytes.fromhex(h160_address)

    # Create the prefixed address
    prefixed_address = bytes("evm:", "utf-8") + address_bytes

    # Calculate checksum
    checksum = hashlib.blake2b(prefixed_address, digest_size=32).digest()

    return ss58_encode(checksum, ss58_format=ss58_format)

