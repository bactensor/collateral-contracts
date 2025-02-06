// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

interface IMetagraph {
    function getValidatorStatus(uint16 netuid, uint16 uid) external view returns (bool);
    function getHotkey(uint16 netuid, uint16 uid) external view returns (bytes32);
}

contract Collateral {
    address public immutable TRUSTEE;
    uint64 public immutable DECISION_TIMEOUT;
    uint64 public immutable MIN_COLLATERAL_INCREASE;

    mapping(uint256 => Reclaim) public reclaims;
    mapping(address => uint256) public collaterals;
    mapping(address => bool) public hasPendingReclaim;
    uint256 private nextReclaimId = 1;

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
    error HasPendingReclaim();
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
        if (hasPendingReclaim[msg.sender]) {
            revert HasPendingReclaim();
        }
        uint256 currentCollateral = collaterals[msg.sender];
        if (currentCollateral < amount) {
            revert InsufficientAmount();
        }
        if (amount < MIN_COLLATERAL_INCREASE && currentCollateral != amount) {
            revert InvalidReclaimAmount();
        }

        uint64 expirationTime = uint64(block.timestamp) + DECISION_TIMEOUT;
        reclaims[nextReclaimId] = Reclaim(msg.sender, amount, expirationTime);
        hasPendingReclaim[msg.sender] = true;

        emit ReclaimProcessStarted(nextReclaimId, msg.sender, amount, expirationTime, url, urlContentMd5Checksum);
        ++nextReclaimId;
    }

    function finalizeReclaim(uint256 reclaimRequestId) external {
        Reclaim memory reclaim = reclaims[reclaimRequestId];
        if (reclaim.amount == 0) {
            revert ReclaimNotFound();
        }
        if (reclaim.denyTimeout >= block.timestamp) {
            revert NotAvailableYet();
        }

        delete hasPendingReclaim[msg.sender];
        delete reclaims[reclaimRequestId];

        if (collaterals[msg.sender] < reclaim.amount) {
            // miner got slashed and can't withdraw
            return;
        }

        collaterals[msg.sender] -= reclaim.amount;

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

        delete hasPendingReclaim[reclaim.miner];
        delete reclaims[reclaimRequestId];

        emit Denied(reclaimRequestId);
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
