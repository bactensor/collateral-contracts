import bittensor
import bittensor_wallet
import eth_account
import eth_utils
from eth_account import messages, Account


def associate_evm_key(
    subtensor: bittensor.Subtensor,
    wallet: bittensor_wallet.Wallet,
    evm_private_key: str,
    netuid: int,
) -> tuple[bool, str]:
    """
    Associate an EVM key with a given wallet for a specific subnet.

    Args:
        subtensor (bittensor.Subtensor): The Subtensor object to use for the transaction.
        wallet (bittensor.wallet): The wallet object containing the hotkey for signing
            the transaction. The wallet.hotkey will be associated with the EVM key.
        evm_private_key (str): The private key corresponding to the EVM address, used
            for signing the message.
        netuid (int): The numerical identifier (UID) of the Subtensor network.
    """
    account = Account.from_key(evm_private_key)

    # subtensor encodes the u64 block number as little endian bytes before hashing
    # https://github.com/opentensor/subtensor/blob/6b86ebf30d3fb83f9d43ed4ce713c43204394e67/pallets/subtensor/src/tests/evm.rs#L44
    # https://github.com/paritytech/parity-scale-codec/blob/v3.6.12/src/codec.rs#L220
    # https://github.com/paritytech/parity-scale-codec/blob/v3.6.12/src/codec.rs#L1439
    block_number = subtensor.get_current_block()
    encoded_block_number = block_number.to_bytes(length=8, byteorder="little")
    hashed_block_number = eth_utils.keccak(encoded_block_number)

    hotkey_bytes: bytes = wallet.hotkey.public_key
    message = hotkey_bytes + hashed_block_number

    signable_message = messages.encode_defunct(message)
    signed_message = eth_account.Account.sign_message(signable_message, account.key)

    call = subtensor.substrate.compose_call(
        call_module="SubtensorModule",
        call_function="associate_evm_key",
        call_params={
            "netuid": netuid,
            "hotkey": wallet.hotkey.ss58_address,
            "evm_key": account.address,
            "block_number": block_number,
            "signature": signed_message.signature.to_0x_hex(),
        },
    )

    return subtensor.sign_and_send_extrinsic(
        call,
        wallet,
        wait_for_inclusion=True,
        wait_for_finalization=True,
        sign_with="hotkey",
    )
