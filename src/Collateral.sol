// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

contract Collateral {
    address public immutable TRUSTEE;
    uint64 public immutable DECISION_TIMEOUT;
    uint64 public immutable MIN_COLLATERAL_INCREASE;

    mapping(uint256 => Reclaim) public reclaims;
    mapping(address => uint256) public collaterals;

    mapping(address => uint256) private collateralUnderPendingReclaims;
    uint256 private nextReclaimId;

    struct Reclaim {
        address miner;
        uint256 amount;
        uint256 denyTimeout;
    }

    event Deposit(address indexed account, uint256 amount);
    event ReclaimProcessStarted(
        uint256 indexed reclaimRequestId,
        address indexed account,
        uint256 amount,
        uint64 expirationTime,
        string url,
        bytes16 urlContentMd5Checksum
    );
    event Reclaimed(uint256 indexed reclaimRequestId, address indexed account, uint256 amount);
    event Denied(uint256 indexed reclaimRequestId);
    event Slashed(address indexed account, uint256 amount);

    error InvalidDepositMethod();
    error CollateralTooLow();
    error InsufficientAmount();
    error InvalidReclaimAmount();
    error ReclaimNotFound();
    error NotAvailableYet();
    error TransferFailed();
    error PastDenyTimeout();
    error NotTrustee();

    constructor(address _trustee, uint64 minCollateralIncrease, uint256 decisionTimeout) {
        TRUSTEE = _trustee;
        MIN_COLLATERAL_INCREASE = minCollateralIncrease;
        DECISION_TIMEOUT = uint64(decisionTimeout);
    }

    modifier onlyTrustee() {
        if (msg.sender != TRUSTEE) {
            revert NotTrustee();
        }
        _;
    }

    receive() external payable {
        revert InvalidDepositMethod();
    }

    fallback() external payable {
        revert InvalidDepositMethod();
    }

    function deposit() external payable {
        if (msg.value < MIN_COLLATERAL_INCREASE) {
            revert InsufficientAmount();
        }

        collaterals[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    function reclaimCollateral(uint256 amount, string calldata url, bytes16 urlContentMd5Checksum) external {
        if (amount == 0) {
            revert InvalidReclaimAmount();
        }
        uint256 currentCollateral = collaterals[msg.sender];
        if (collateralUnderPendingReclaims[msg.sender] + amount > collaterals[msg.sender]) {
            revert CollateralTooLow();
        }
        if (amount < MIN_COLLATERAL_INCREASE && currentCollateral != amount) {
            revert InvalidReclaimAmount();
        }

        uint64 expirationTime = uint64(block.timestamp) + DECISION_TIMEOUT;
        reclaims[++nextReclaimId] = Reclaim(msg.sender, amount, expirationTime);
        collateralUnderPendingReclaims[msg.sender] += amount;

        emit ReclaimProcessStarted(nextReclaimId, msg.sender, amount, expirationTime, url, urlContentMd5Checksum);
    }

    function finalizeReclaim(uint256 reclaimRequestId) external {
        Reclaim memory reclaim = reclaims[reclaimRequestId];
        if (reclaim.amount == 0) {
            revert ReclaimNotFound();
        }
        if (reclaim.denyTimeout >= block.timestamp) {
            revert NotAvailableYet();
        }

        delete reclaims[reclaimRequestId];
        collateralUnderPendingReclaims[reclaim.miner] -= reclaim.amount;

        if (collaterals[reclaim.miner] < reclaim.amount) {
            // miner got slashed and can't withdraw
            return;
        }

        collaterals[reclaim.miner] -= reclaim.amount;

        emit Reclaimed(reclaimRequestId, reclaim.miner, reclaim.amount);
        (bool success,) = payable(reclaim.miner).call{value: reclaim.amount}("");
        if (!success) {
            revert TransferFailed();
        }
    }

    function denyReclaimRequest(uint256 reclaimRequestId) external onlyTrustee {
        Reclaim memory reclaim = reclaims[reclaimRequestId];
        if (reclaim.amount == 0) {
            revert ReclaimNotFound();
        }
        if (reclaim.denyTimeout < block.timestamp) {
            revert PastDenyTimeout();
        }

        collateralUnderPendingReclaims[reclaim.miner] -= reclaim.amount;
        emit Denied(reclaimRequestId);

        delete reclaims[reclaimRequestId];
    }

    function slashCollateral(address miner, uint256 amount) external onlyTrustee {
        if (collaterals[miner] < amount) {
            revert InsufficientAmount();
        }
        collaterals[miner] -= amount;
        // burn the collateral
        (bool success,) = payable(address(0)).call{value: amount}("");
        if (!success) {
            revert TransferFailed();
        }

        emit Slashed(miner, amount);
    }
}
