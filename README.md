# Collateral Smart Contract for Bittensor

> **Purpose**: Manage miner collaterals in the Bittensor ecosystem, allowing validators to slash misbehaving miners.
>
> **Design**: One collateral contract per validator and subnet.

> **About This Contract**
>
> This smart contract is **generic** and can be used by **any Bittensor subnet** to manage miner collateral.
> However, the **usage guides in this README reflect the recommended integration pattern** pioneered by the [ComputeHorde](https://github.com/ComputeHorde) subnet (`sn12`).
> Subnets adopting the same approach only need to adjust the `--netuid` parameter in setup scripts.

## Overview

This contract creates a **trust-minimized interaction** between miners and validators in the Bittensor ecosystem. 
**One contract per validator per subnet** ensures clear accountability for each validator's collateral pool.

- **Miners Lock Collateral**
  
  Miners demonstrate their commitment by staking collateral into the validator's contract.

- **Collateral-Based Prioritization**

  Validators may choose to favor miners with higher collateral when assigning tasks, incentivizing greater stakes for reliable performance.

- **Arbitrary Slashing**
  
  Validators can penalize a misbehaving miner by slashing any portion of the miner's collateral.

- **Automatic Release**

  If a validator does not respond to a miner's reclaim request within a configured deadline, the miner can reclaim their stake, preventing indefinite lock-ups.

- **Trustless & Auditable**
  
  All operations (deposits, reclaims, slashes) are publicly logged on-chain, enabling transparent oversight for both validators and miners.

- **Off-Chain Justifications**

  Functions `slashCollateral`, `reclaimCollateral`, and `denyReclaim` include URL fields (and content MD5 checksums) to reference off-chain
  explanations or evidence for each action, ensuring decisions are transparent and auditable.

- **Configurable Minimum Bond & Decision Deadline**
  
  Defines a minimum stake requirement and a strict timeline for validator responses.

> **Important Notice on Addressing**
>
> This contract uses **H160 (Ethereum) addresses** for both miner and validator identities.
> - Before interacting with the contract (depositing, slashing, reclaiming, etc.), **all parties must have an Ethereum wallet** (including a plain text private key) to sign the required transactions.
> - Each H160 wallet used with this contract **should be** explicitly associated with its corresponding **SS58 hotkey**, using on-chain mechanisms provided by Subtensor. 
> - Use [`scripts/associate_evm_key.py`](/scripts/associate_evm_key.py) to perform the association.
> - This ensures that validators and miners can reliably link wallet actions to Bittensor identities.

> **Transaction Fees**
>
> All on-chain actions (deposits, slashes, reclaims, etc.) consume gas, so **both miners and validators must hold enough TAO in their Ethereum (H160) wallets** to cover transaction fees.
> - Make sure to keep a sufficient balance to handle any deposits, reclaims, or slashes you need to perform.
> - Convert H160 to SS58 ([`scripts/h160_to_ss58.py`](/scripts/h160_to_ss58.py) to transfer TAO to it.
> - You can transfer TAO back to your SS58 wallet when no more contract interactions are required. See [`scripts/send_to_ss58_precompile.py`](/script/send_to_ss58_precompile.py).

## Demo

[![asciicast](https://asciinema.org/a/TwXIpf0SffBjg8mZstaFUuA2L.svg)](https://asciinema.org/a/TwXIpf0SffBjg8mZstaFUuA2L)

## Collateral Smart Contract Lifecycle

Below is a typical sequence for integrating and using this collateral contract within a Bittensor subnet:

- **Subnet Integration**
   - The subnet owner **updates validator software** to prioritize miners with higher collateral when assigning tasks.
   - Validators adopt this updated code and prepare to enforce collateral requirements.

- **Validator Deployment**
   - The validator **creates an Ethereum (H160) wallet**, associates it with their hotkey, and funds it with enough TAO to cover transaction fees.
   - The validator **deploys the contract**, requiring participating miners to stake collateral.
   - The validator **publishes the contract address** on-chain, allowing miners to discover and verify it.
   - Once ready, the validator **enables collateral-required mode** and prioritizes miners based on their locked amounts.

- **Miner Deposit**
   - Each miner **creates an Ethereum (H160) wallet**, associates it with their hotkey, and funds it with enough TAO for transaction fees.
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
Refer to the repository's [`scripts/`](/scripts/) folder for sample implementations and helper scripts.

### Recommended Miner Integration Guide (as used by ComputeHorde)

<details>
<summary>Click to expand recommended miner setup flow</summary>

This is the collateral workflow currently used by **ComputeHorde** miners.
Other subnets may follow the same process — no changes are needed beyond the `--netuid` value in setup.

#### **1. Setup with `setup_evm.sh`**

Run the script on a machine that has access to your **coldkey**, to:

- **Create or reuse** an H160 wallet under `~/.bittensor/wallet/coldkey/h160/hotkey`.
- **Transfer TAO** to the wallet:
  - At least **1 TAO per validator** you plan to stake with (this is the current minimum for ComputeHorde).
  - Plus additional TAO to cover **gas fees** for deposit, reclaim, and finalize transactions — we recommend **~0.2 TAO extra**.
- **Associate** the H160 wallet with your miner hotkey on the appropriate `--netuid`.

> Note: This is the same script validators use, but without the `--deploy` flag.
> You do **not** need to deploy a contract or copy the private key to your miner machine.

#### **2. Discover Validator Contracts**

To find available validators:

- Run [`scripts/list_contracts.py`](scripts/list_contracts.py) to query your subnet’s **knowledge commitments**.
- It will list all known validator contracts along with the collateral amount you’ve deposited (if any).

#### **3. Choose Trusted Validators**

- Review the listed validators and decide which ones you trust to act fairly and slash responsibly.
- You can choose one or multiple validators — just be sure to have enough TAO for each one.

#### **4. Verify Contracts**

Before depositing:

- Use [`scripts/verify_contract.py`](scripts/verify_contract.py) to confirm that a validator’s contract:
  - Is built from this repository,
  - Matches the expected parameters (subnet ID, trustee, etc.).

This ensures you are not locking funds into a malicious or fake contract.

#### **5. Deposit Collateral**

- Run [`scripts/deposit_collateral.py`](scripts/deposit_collateral.py) for each validator you trust.
- Confirm on-chain that the deposit succeeded using [`scripts/get_miners_collateral.py`](scripts/get_miners_collateral.py).

#### **6. Receive Tasks and Monitor the Network**

- You will begin receiving **organic task assignments** from validators using your staked collateral as a signal.
- Periodically re-run `list_contracts.py` to discover new validators or updated contracts you may want to deposit into.

#### **7. Reclaim and Withdraw**

When you want to exit:

- Use [`scripts/reclaim_collateral.py`](scripts/reclaim_collateral.py) to initiate withdrawal.
- After the timeout period (if not denied), use [`scripts/finalize_reclaim.py`](scripts/finalize_reclaim.py) to unlock your collateral.
- Finally, use [`scripts/send_to_ss58_precompile.py`](scripts/send_to_ss58_precompile.py) to move your TAO back to your SS58 wallet.

> Reminder: None of these steps require the H160 private key to be present on your miner machine.

</details>

### As a Miner, you can:

- **Deposit Collateral**
  If you plan to stake for multiple validators, simply repeat these steps for each one:
  - Obtain the validator's contract address (usually via tools provided by the subnet owner).
  - Verify that code deployed at the address is indeed the collateral smart contract, the trustee and netuid kept inside are as expected - see [`scripts/verify_contract.py`](/scripts/verify_contract.py).
  - Run [`scripts/deposit_collateral.py`](/scripts/deposit_collateral.py) to initiate the deposit transaction with your specified amount of $TAO.
  - Confirm on-chain that your collateral has been successfully locked for that validator - [`scripts/get_miners_collateral.py`](/scripts/get_miners_collateral.py)

- **Reclaim Collateral**
  - Initiate the reclaim process by running [`scripts/reclaim_collateral.py`](/scripts/reclaim_collateral.py) with your desired withdrawal amount.
  - Wait for the validator's response or for the configured inactivity timeout to pass.
  - If the validator does not deny your request by the deadline, run [`scripts/finalize_reclaim.py`](/scripts/finalize_reclaim.py) to unlock and retrieve your collateral.
  - Verify on-chain that your balance has been updated accordingly.

### Recommended Validator Integration Guide (as used by ComputeHorde)

<details>
<summary>Click to expand recommended validator setup flow</summary>

This is the validator integration flow currently used by the **ComputeHorde** subnet (`sn12`).
Other subnets are encouraged to adopt the same model — only the `--netuid` parameter needs to be adjusted.

#### **1. Setup with `setup_evm.sh --deploy`**

Run the helper script on a machine that has access to your validator coldkey:

- **Creates or reuses** a validator H160 wallet (`~/.bittensor/wallet/coldkey/h160/hotkey`):
  - Use `--reuse` to keep an existing identity.
  - Use `--overwrite` **with caution** – this deletes and replaces the private key (and thus access to any TAO previously sent to it).
- **Transfers funds** to the wallet (recommended: at least **1 TAO** to start).
- **Associates** the H160 with the validator’s SS58 hotkey on the target `--netuid`.
- **Deploys the collateral contract** to Ethereum.
- If on **mainnet**, it also **verifies the contract on [evm.taostats.io](https://evm.taostats.io)** for public transparency.
- **Publishes the contract address** as a **knowledge commitment** on-chain, enabling miners and other tools to discover and verify it.

#### **2. Transfer H160 Key to Validator Node**

Move the generated H160 key file (`hotkey`) to your validator machine (e.g., `sn12`).
You do **not** need to transfer the coldkey — the private key file is sufficient for all contract interactions.

#### **3. Validator Code Uses the Contract**

The validator code provided by the subnet owner:

- **Reads the published knowledge commitment** to get the contract address.
- **Prioritizes miners** based on their staked collateral.
- **Performs automated slashing** when cross-validation detects incorrect responses:
  - Initially slashes **tiny amounts** to calibrate the logic.
  - Later increases slashing severity to discourage misbehavior.

#### **4. Maintain Sufficient TAO for Gas**

Slashing operations consume gas on Ethereum.
Validators must keep their H160 wallet funded to support this:

- A **Grafana chart** will monitor the H160 wallet balance.
- Top up when needed to avoid disruptions in automated enforcement.

#### **5. Manual Slashing & Reclaim Denials (Optional)**

In rare cases where cheating is **suspected but not yet confirmed** by automation:

- You may **manually deny reclaim requests** from the suspected miner.
- If confirmed, issue a **manual slash**.
- If false alarm, stop denying and allow the reclaim to proceed normally.

</details>

### As a Validator, you can:

- **Deploy the Contract**
  - Install [Foundry](https://book.getfoundry.sh/).
  - Clone this repository.
  - Compile and deploy the contract, use [`deploy.sh`](deploy.sh) with your details as arguments.
  - Record the deployed contract address and publish it via a subnet-owner-provided tool so that miners can discover and verify it.

- **Enable Regular Operation**
  - Enable the deployed contract address in your validator's code (provided by the subnet owner), so that
    - task assignment prioritizes miners with higher collateral balances.
    - misbehaviour checks causing slashing are automated.

- **Monitor Activity**
  - Use Ethereum JSON-RPC API or a blockchain explorer to view events (`Deposit`, `ReclaimProcessStarted`, `Slashed`, `Reclaimed`).
  - Query contract mappings (`collaterals`, `reclaims`) to check staked amounts and pending reclaim requests.
  - Maintain a local script or UI to stay updated on changes in miner collateral.

- **Manually Deny a Reclaim**
  - Identify the relevant `reclaimRequestId` (from `ReclaimProcessStarted` event, for example).
  - Use [`scripts/deny_reclaim.py`](scripts/deny_reclaim.py) (calling the contract's `denyReclaim(reclaimRequestId)`) before the deadline.
  - Verify on-chain that the reclaim request is removed and the miner's `hasPendingReclaim` is reset to `false`.

- **Manually Slash Collateral**
  - Confirm miner misconduct based on subnetwork rules (e.g., invalid blocks, spam, protocol violations).
  - Use [`scripts/slash_collateral.py`](scripts/slash_collateral.py) (calling the contract's `slashCollateral(miner, slashAmount)`) to penalize the miner by reducing their staked amount.
  - Verify the transaction on-chain and confirm the miner's `collaterals[miner]` value has changed.

### As a Subnet Owner, you can

- **Provide Deployment Tools for Validators**
  
  Offer a script <!--(e.g. built on top of [`scripts/deploy.sh`](todo-link))--> to help validators:
  - Create H160 wallet & assosiate it with their SS58.
  - Transfer Tao.
  - Deploy the contract.
  - Publish the resulting contract address (e.g., as a knowledge commitment) so miners can easily verify and deposit collateral.

- **Provide Tools for Miners**
  
  Offer a script that retrieves a list of active validator contract addresses from your on-chain registry or other trusted source.
  This helps miners discover the correct contract for depositing collateral.

- **Track Miner Collateral Usage**
  - Query each validator's contract (using, for example, a script based on [`scripts/get_collaterals.py`](/scripts/get_collaterals.py)) to see how much collateral is staked by each miner.
  - Aggregate this data into a subnet-wide dashboard for real-time oversight of miner participation.
    <!-- - Check out the [ComputeHorde Grafana chart](https://grafana.bactensor.io/d/subnet/metagraph-subnet?var-subnet=12) for a real-world example.-->

- **Facilitate Result-Based Slashing**
  
  Provide validators with automated checks that periodically verify a small subset (e.g., 1–2%) of the miner's submissions.
  If a miner's responses fall below the desired quality threshold, the code should call `slashCollateral()` to penalize substandard performance.
  For example, in the [ComputeHorde SDK](https://sdk.computehorde.io/), slashing is triggered via the [`report_cheated_job()`](https://sdk.computehorde.io/master/api/client.html#compute_horde_sdk.v1.ComputeHordeClient.report_cheated_job) method.

- **Facilitate Collateral Verification**
  
  Provide validator code that checks each miner's staked amount before assigning tasks. This code can:
  - Prioritize miners who have staked more collateral.
  - Reject miners who do not meet a minimum collateral requirement.

  By coupling task assignment with the collateral balance, the subnetwork ensures more consistent performance and discourages low-quality or malicious contributions.


## Full Script Reference

Below is a full list of helper scripts available in the [`scripts/`](scripts/) directory.
Most of them are already linked inline in the **Usage Guides** above, but this section provides a complete overview for reference or discovery.

### **Getting Started & Finalizing**

- [`setup_evm.py`](scripts/setup_evm.py) – End-to-end setup script for both miners and validators: generates or reuses an H160 wallet, associates it with a hotkey, and funds it with TAO. Validators continue by deploying the contract and publishing its address.
- [`send_to_ss58_precompile.py`](scripts/send_to_ss58_precompile.py) – Transfers TAO from an H160 wallet back to an SS58 address once contract interactions are complete.

### **Contract Interaction – Miners**

- [`deposit_collateral.py`](scripts/deposit_collateral.py) – Deposits a specified amount of TAO into a validator’s collateral contract.
- [`reclaim_collateral.py`](scripts/reclaim_collateral.py) – Initiates the reclaim process to withdraw collateral.
- [`finalize_reclaim.py`](scripts/finalize_reclaim.py) – Completes a reclaim after the timeout, unlocking collateral if the validator has not denied it.
- [`verify_contract.py`](scripts/verify_contract.py) – Verifies that a validator’s contract matches expected parameters (e.g., correct subnet and trustee) before depositing.
- [`list_contracts.py`](scripts/list_contracts.py) – Scans the on-chain knowledge commitments for a subnet and returns a list of all validator contract addresses and their associated hotkeys, along with your deposit amounts.

### **Contract Interaction – Validators**

- [`slash_collateral.py`](scripts/slash_collateral.py) – Penalizes a miner by slashing a specified amount of their staked collateral.
- [`deny_request.py`](scripts/deny_request.py) – Denies a pending reclaim request, preventing the miner from recovering their stake.
- [`get_collaterals.py`](scripts/get_collaterals.py) – Lists all collateral deposits that occurred within a given block range.
- [`get_reclaim_requests.py`](scripts/get_reclaim_requests.py) – Lists all reclaim requests made during a specified block range.

### **Address Management & General Utilities**

- [`generate_keypair.py`](scripts/generate_keypair.py) – Generates a new Ethereum (H160) keypair.
- [`associate_evm_key.py`](scripts/associate_evm_key.py) – Associates an H160 wallet with a Bittensor SS58 hotkey on-chain.
- [`h160_to_ss58.py`](scripts/h160_to_ss58.py) – Converts an Ethereum H160 address to its corresponding SS58 format.
- [`get_hotkey_association.py`](scripts/get_hotkey_association.py) – Retrieves the H160 address associated with a given hotkey.
- [`get_all_associations.py`](scripts/get_all_associations.py) – Lists all H160–SS58 associations for a specific subnet.
- [`get_current_block.py`](scripts/get_current_block.py) – Retrieves the current block number from the Ethereum network.
- [`get_balance.py`](scripts/get_balance.py) – Checks the TAO balance of a given H160 wallet.
- [`get_miners_collateral.py`](scripts/get_miners_collateral.py) – Retrieves the amount of collateral a given miner has deposited to a specific validator’s contract.
  *(Used internally by other scripts like `list_contracts.py`, but can also be used directly for targeted queries.)*
