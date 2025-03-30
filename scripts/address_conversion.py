#!/usr/bin/env python3
from substrateinterface import Keypair


def privkey_to_ss58(private_key: str) -> str:
    """
    Convert private key to SS58 address.

    Args:
        private_key (str): The private key in hex format (with or without 0x prefix)

    Returns:
        str: The SS58 address

    Raises:
        ValueError: If the private key is invalid
    """
    try:
        # Remove 0x prefix if present
        if private_key.startswith("0x"):
            private_key = private_key[2:]
            
        # Create a Keypair from the private key
        keypair = Keypair(private_key=bytes.fromhex(private_key), ss58_format=42)
        
        # Get the SS58 address
        return keypair.ss58_address

    except Exception as e:
        raise ValueError(f"Error converting private key to SS58 address: {str(e)}")


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
