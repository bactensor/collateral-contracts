#!/usr/bin/env python3
from substrateinterface import Keypair
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


def ss58_to_h160(ss58_address: str) -> str:
    """
    Convert SS58 address to H160 (Ethereum) address.
    
    Args:
        ss58_address (str): The SS58 address to convert
        
    Returns:
        str: The H160 address in hex format
    """
    try:
        # Create a Keypair from the SS58 address
        keypair = Keypair(ss58_address=ss58_address)
        
        # Get the public key (32 bytes)
        public_key = keypair.public_key
        
        # Convert to H160 (take last 20 bytes of the public key)
        h160 = public_key[-20:].hex()
        
        # Add '0x' prefix
        return f"0x{h160}"
    
    except Exception as e:
        print(f"Error converting address: {str(e)}")
        return None


# https://github.com/opentensor/evm-bittensor/blob/main/examples/address-mapping.js
def h160_to_ss58(h160_address):
    # Ensure the address is in bytes
    if h160_address.startswith("0x"):
        h160_address = h160_address[2:]

    # Convert hex string to bytes
    address_bytes = bytes.fromhex(h160_address)

    # Create the prefixed address
    prefixed_address = bytes('evm:', 'utf-8') + address_bytes

    # Calculate checksum
    checksum = hashlib.blake2b(prefixed_address, digest_size=32).digest()[:2]

    # Create the full address with checksum
    full_address = prefixed_address + checksum
    
    # Encode in the Base58 format
    ss58_address = base58.b58encode(full_address)

    return ss58_address.decode('utf-8')
