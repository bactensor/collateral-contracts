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

## Usage Guides

Below are step-by-step instructions tailored to **miners**, **validators**, and **subnet owners**.
These guides cover contract deployment, collateral management, slashing procedures, and more.
Refer to the repository’s `scripts/` folder for sample implementations and helper scripts.

## As a Miner, you can:

- **Deposit Collateral**
  If you plan to stake for multiple validators, simply repeat these steps for each one:
  1. Obtain the validator’s contract address (usually via tools provided by the subnet owner).
  2. Run [`scripts/deposit.sh`](./scripts/deposit.sh) (or a similar tool) to initiate the deposit transaction.
     - This script checks the contract address, verifies its contents, and calls the `deposit()` function with your specified amount of $TAO.
  3. Confirm on-chain that your collateral has been successfully locked for that validator.

- **Reclaim Collateral**
  1. Initiate the reclaim process by running [`scripts/start_reclaim_process.sh`](./scripts/start_reclaim_process.sh) with your desired withdrawal amount.
  2. Wait for the validator’s response or for the configured inactivity timeout to pass.
  3. If the validator does not deny your request by the deadline, run [`scripts/finalize_reclaim.sh`](./scripts/finalize_reclaim.sh) to unlock and retrieve your collateral.
  4. Verify on-chain that your balance has been updated accordingly.


### As a Validator, you can:

- **Deploy the Contract**
  1. Clone this repository and install dependencies (using [Foundry](https://book.getfoundry.sh/)):
     ```bash
     forge build
     ```
  2. Compile and deploy the contract, use `scripts/deploy.sh` with your details as arguments.
  3. Record the deployed contract address and publish it via a subnet-owner-provided tool so that miners can discover and verify it.

- **Enable Regular Operation**
  1. Enable the deployed contract address in your validator’s code (provided by the subnet owner), so that
    - task assignment prioritizes miners with higher collateral balances.
    - misbehaviour checks causing slashing are automated.

- **Monitor Activity**
  1. Use the contract’s public functions or a blockchain explorer to view events (`Deposit`, `ReclaimProcessStarted`, `Slashed`, `Reclaimed`).
  2. Query contract mappings (`collaterals`, `reclaims`) to check staked amounts and pending reclaim requests.
  3. Maintain a local script or UI to stay updated on changes in miner collateral.

- **Manually Deny a Reclaim**
  1. Identify the relevant `reclaimRequestId` (from `ReclaimProcessStarted` event, for example).
  2. Call `denyReclaim(reclaimRequestId)` before the deadline.
  3. Verify on-chain that the reclaim request is removed and the miner’s `hasPendingReclaim` is reset to `false`.

- **Manually Slash Collateral**
  1. Confirm miner misconduct based on subnetwork rules (e.g., invalid blocks, spam, protocol violations).
  2. Call `slashCollateral(miner, slashAmount)` to penalize the miner by reducing their staked amount.
  3. Verify the transaction on-chain and confirm the miner’s `collaterals[miner]` value has changed.

### As a Subnet Owner, you can

- **Provide Deployment Tools for Validators**
  Offer a script <!--(e.g. built on top of [`scripts/deploy.sh`](todo-link))--> to help validators:
  1. **Deploy** the contract.
  2. **Publish** the resulting contract address (e.g., as a knowledge commitment) so miners can easily verify and deposit collateral.

- **Provide Tools for Miners**
  Offer a script that retrieves a list of active validator contract addresses from your on-chain registry or other trusted source.
  This helps miners discover the correct contract for depositing collateral.

- **Track Miner Collateral Usage**
  Query each validator’s contract <!---(using, for example, an off-chain script based on [`scripts/query.sh`](todo-link))--> to see how much collateral is staked by each miner.
  Aggregate this data into a subnet-wide dashboard for real-time oversight of miner participation.
  <!-- - Check out the [ComputeHorde Grafana chart](https://grafana.bactensor.io/d/subnet/metagraph-subnet?var-subnet=12) for a real-world example.-->

- **Facilitate Result-Based Slashing**
  Provide validators with automated checks that periodically verify a small subset (e.g., 1–2%) of the miner’s submissions.
  If a miner’s responses fall below the desired quality threshold, the code calls `slashCollateral()` to penalize substandard performance.
  <!--For example, in the [ComputeHorde SDK](todo-link), slashing is triggered via the `report_cheated_job()` method.-->

- **Facilitate Collateral Verification**
  Provide validator code that checks each miner’s staked amount before assigning tasks. This code can:
  1. **Prioritize** miners who have staked more collateral.
  2. **Reject** miners who do not meet a minimum collateral requirement.

  By coupling task assignment with the collateral balance, the subnetwork ensures more consistent performance and discourages low-quality or malicious contributions.


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
