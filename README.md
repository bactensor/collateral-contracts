# Collateral Smart Contract for Bittensor

- **Purpose**: Manage miner collaterals in the Bittensor ecosystem, allowing validators to slash misbehaving miners.

- **Design**: One collateral contract per validator and subnet.

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

## Collateral Smart Contract Lifecycle

Below is a typical sequence for integrating and using this collateral contract within a Bittensor subnet:

1. **Subnetwork Integration**
   - The subnet owner updates validator code to verify miners have posted collateral before assigning tasks.
   - Validators adopt the updated code and prepare for collateral enforcement.

2. **Validator Deployment**
   - A validator **deploys** this contract to require collateral from participating miners.
   - The validator **publishes** the contract address on-chain for miners to discover.
   - Once ready, the validator **enables** a “collateral-required” mode and may prioritize miners who have staked higher amounts.

3. **Miner Participation**

   - Miners **retrieve** the validator’s contract address from the chain.
   - They **verify** the contract references the correct validator address and is legitimate.
   - After confirmation, miners **deposit** collateral by calling the contract’s `deposit` function.

4. **Slashing Misbehaving Miners**
   - If a miner is caught breaking rules (e.g., returning invalid responses), the validator calls `slashCollateral` to reduce that miner’s staked amount.

5. **Reclaiming Collateral**
   - When miners want to withdraw their deposit, they call `reclaimCollateral`.
   - If the validator does not deny the request before the deadline, miners (or anyone) can call `finalizeReclaim` to unlock and return the collateral.

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
