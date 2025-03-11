# Collateral Smart Contract for Bittensor

> * **Purpose**: Manage miner collaterals in the Bittensor ecosystem, allowing validators to slash misbehaving miners.
> * **Design**: One collateral contract per validator and subnet.

## Overview

This contract creates a **trust-minimized interaction** between miners and validators in the Bittensor ecosystem. 
**One contract per validator per subnet** ensures clear accountability for each validator's collateral pool.

- **Miners Lock Collateral**
  
  Miners demonstrate their commitment by staking collateral into the validator's contract.

- **Miner Prioritization**

  Validators may choose to favor miners with higher collateral when assigning tasks, incentivizing greater stakes for reliable performance.

- **Arbitrary Slashing**
  
  Validators can penalize a misbehaving miner by slashing any portion of the miner's collateral.

- **Automatic Release**

  If a validator does not respond to a miner's reclaim request within a configured deadline, the miner can reclaim their stake, preventing indefinite lock-ups.

- **Configurable Minimum Bond & Decision Deadline**
  
  Defines a minimum stake requirement and a strict timeline for validator responses.

- **Trustless & Auditable**
  
  All operations (deposits, reclaims, slashes) are publicly logged on-chain, enabling transparent oversight for both validators and miners.

> **Important Notice on Addressing**
> This contract uses **H160 (Ethereum) addresses** for both miner and validator identities.
> - Before interacting with the contract (depositing, slashing, reclaiming, etc.), **all parties must have an Ethereum wallet** (including a plain text private key) to sign the required transactions.
> - An association between these H160 wallet addresses and the respective **SS58 hotkeys** (used in Bittensor) is **strongly recommended** so validators can reliably identify miners.
> - Best practices for managing and verifying these address associations are still under development within the broader Bittensor ecosystem.


## Collateral Smart Contract Lifecycle

Below is a typical sequence for integrating and using this collateral contract within a Bittensor subnet:

- **Subnet Integration**
   - The subnet owner **updates validator software** to prioritize miners with higher collateral when assigning tasks.
   - Validators adopt this updated code and prepare to enforce collateral requirements.

- **Validator Deployment**
   - A validator **deploys the contract**, requiring participating miners to stake collateral.
   - The validator **publishes the contract address** on-chain, allowing miners to discover and verify it.
   - Once ready, the validator **enables collateral-required mode** and prioritizes miners based on their locked amounts.

- **Miner Deposit**
   - Miners **retrieve** the validator's contract address from the chain or another trusted source.
   - They **verify** the contract is indeed associated with the intended validator.
   - Upon confirmation, miners **deposit** collateral by calling the contract's `deposit()` function.

- **Slashing Misbehaving Miners**
   - If a miner is found violating subnet rules (e.g., returning invalid responses), the validator **calls** `slashCollateral()` to penalize the miner by reducing their staked amount.

- **Reclaiming Collateral**
   - When miners wish to withdraw their stake, they **initiate a reclaim** by calling `reclaimCollateral()`.
   - If the validator does not deny the request before the deadline, miners (or anyone) can **finalize** it using `finalizeReclaim()`, thus unlocking and returning the collateral.



## Usage Guides

Below are step-by-step instructions tailored to **miners**, **validators**, and **subnet owners**.
These guides cover contract deployment, collateral management, slashing procedures, and more.
Refer to the repository's `scripts/` folder for sample implementations and helper scripts.

## As a Miner, you can:

- **Deposit Collateral**
  If you plan to stake for multiple validators, simply repeat these steps for each one:
  - Obtain the validator's contract address (usually via tools provided by the subnet owner).
  - Run [`scripts/deposit.sh`](./scripts/deposit.sh) (or a similar tool) to initiate the deposit transaction.
    This script checks the contract address, verifies its contents, and calls the `deposit()` function with your specified amount of $TAO.
  - Confirm on-chain that your collateral has been successfully locked for that validator.

- **Reclaim Collateral**
  - Initiate the reclaim process by running [`scripts/start_reclaim_process.sh`](./scripts/start_reclaim_process.sh) with your desired withdrawal amount.
  - Wait for the validator's response or for the configured inactivity timeout to pass.
  - If the validator does not deny your request by the deadline, run [`scripts/finalize_reclaim.sh`](./scripts/finalize_reclaim.sh) to unlock and retrieve your collateral.
  - Verify on-chain that your balance has been updated accordingly.


### As a Validator, you can:

- **Deploy the Contract**
  - Clone this repository and install dependencies (using [Foundry](https://book.getfoundry.sh/)):
     ```bash
     forge build
     ```
  - Compile and deploy the contract, use `scripts/deploy.sh` with your details as arguments.
  - Record the deployed contract address and publish it via a subnet-owner-provided tool so that miners can discover and verify it.

- **Enable Regular Operation**
  - Enable the deployed contract address in your validator's code (provided by the subnet owner), so that
    - task assignment prioritizes miners with higher collateral balances.
    - misbehaviour checks causing slashing are automated.

- **Monitor Activity**
  - Use the contract's public functions or a blockchain explorer to view events (`Deposit`, `ReclaimProcessStarted`, `Slashed`, `Reclaimed`).
  - Query contract mappings (`collaterals`, `reclaims`) to check staked amounts and pending reclaim requests.
  - Maintain a local script or UI to stay updated on changes in miner collateral.

- **Manually Deny a Reclaim**
  - Identify the relevant `reclaimRequestId` (from `ReclaimProcessStarted` event, for example).
  - Use `scripts/deny_reclaim.sh` (calling the contract's `denyReclaim(reclaimRequestId)`) before the deadline.
  - Verify on-chain that the reclaim request is removed and the miner's `hasPendingReclaim` is reset to `false`.

- **Manually Slash Collateral**
  - Confirm miner misconduct based on subnetwork rules (e.g., invalid blocks, spam, protocol violations).
  - Use `scripts/slash_collateral.sh` (calling the contract's `slashCollateral(miner, slashAmount)`) to penalize the miner by reducing their staked amount.
  - Verify the transaction on-chain and confirm the miner's `collaterals[miner]` value has changed.

### As a Subnet Owner, you can

- **Provide Deployment Tools for Validators**
  Offer a script <!--(e.g. built on top of [`scripts/deploy.sh`](todo-link))--> to help validators:
  - Deploy the contract.
  - Publish the resulting contract address (e.g., as a knowledge commitment) so miners can easily verify and deposit collateral.

- **Provide Tools for Miners**
  Offer a script that retrieves a list of active validator contract addresses from your on-chain registry or other trusted source.
  This helps miners discover the correct contract for depositing collateral.

- **Track Miner Collateral Usage**
  - Query each validator's contract <!---(using, for example, an off-chain script based on [`scripts/query.sh`](todo-link))--> to see how much collateral is staked by each miner.
  - Aggregate this data into a subnet-wide dashboard for real-time oversight of miner participation.
    <!-- - Check out the [ComputeHorde Grafana chart](https://grafana.bactensor.io/d/subnet/metagraph-subnet?var-subnet=12) for a real-world example.-->

- **Facilitate Result-Based Slashing**
  Provide validators with automated checks that periodically verify a small subset (e.g., 1–2%) of the miner's submissions.
  If a miner's responses fall below the desired quality threshold, the code calls `slashCollateral()` to penalize substandard performance.
  <!--For example, in the [ComputeHorde SDK](todo-link), slashing is triggered via the `report_cheated_job()` method.-->

- **Facilitate Collateral Verification**
  Provide validator code that checks each miner's staked amount before assigning tasks. This code can:
  - Prioritize miners who have staked more collateral.
  - Reject miners who do not meet a minimum collateral requirement.

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

### Deploy
Please check contents of `deploy.sh`.
