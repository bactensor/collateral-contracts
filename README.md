# Collateral Smart Contract for Bittensor

> **Purpose**: Manage miner collaterals in the Bittensor ecosystem, allowing validators to slash misbehaving miners.
> **Design**: One collateral contract per validator and subnet.

---

## Overview

This contract creates a **trust-minimized interaction** between miners and validators in the Bittensor ecosystem. 
**One contract per validator per subnet** ensures clear accountability for each validator’s collateral pool.

- **Miners Lock Collateral**
  Miners demonstrate their commitment by staking collateral into the validator’s contract.

- **Automatic Release**
  If a validator does not respond to a miner’s reclaim request within a configured deadline, the miner can reclaim their stake, preventing indefinite lock-ups.

- **Arbitrary Slashing**
  Validators can penalize a misbehaving miner by slashing any portion of the miner’s collateral.

- **Configurable Minimum Bond & Decision Deadline**
  Defines a minimum stake requirement and a strict timeline for validator responses.

- **Trustless & Auditable**
  All operations (deposits, reclaims, slashes) are publicly logged on-chain, enabling transparent oversight for both validators and miners.

---
## Foundry

**Foundry is a blazing fast, portable and modular toolkit for Ethereum application development written in Rust.**

Foundry consists of:

-   **Forge**: Ethereum testing framework (like Truffle, Hardhat and DappTools).
-   **Cast**: Swiss army knife for interacting with EVM smart contracts, sending transactions and getting chain data.
-   **Anvil**: Local Ethereum node, akin to Ganache, Hardhat Network.
-   **Chisel**: Fast, utilitarian, and verbose solidity REPL.

## Documentation

https://book.getfoundry.sh/

## Usage

### Build

```shell
$ forge build
```

### Test

```shell
$ forge test
```

### Format

```shell
$ forge fmt
```

### Gas Snapshots

```shell
$ forge snapshot
```

### Anvil

```shell
$ anvil
```

### Deploy

```shell
$ forge script script/Counter.s.sol:CounterScript --rpc-url <your_rpc_url> --private-key <your_private_key>
```

### Cast

```shell
$ cast <subcommand>
```

### Help

```shell
$ forge --help
$ anvil --help
$ cast --help
```
