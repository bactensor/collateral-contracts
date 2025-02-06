// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

contract Collateral {
    uint16 public immutable NETUID;
    address public immutable TRUSTEE;
    uint64 public immutable DECISION_TIMEOUT;
    uint256 public immutable MIN_COLLATERAL_INCREASE;

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
    event Denied(uint256 indexed reclaimRequestId, string url, bytes16 urlContentMd5Checksum);
    event Slashed(address indexed account, uint256 amount, string url, bytes16 urlContentMd5Checksum);

    error AmountZero();
    error BeforeDenyTimeout();
    error InsufficientAmount();
    error InvalidDepositMethod();
    error NotTrustee();
    error PastDenyTimeout();
    error ReclaimAmountTooLarge();
    error ReclaimAmountTooSmall();
    error ReclaimNotFound();
    error TransferFailed();

    /// @notice Initializes a new Collateral contract with specified parameters
    /// @param netuid The netuid of the subnet
    /// @param trustee H160 address of the trustee who has permissions to slash collateral or deny reclaim requests
    /// @param minCollateralIncrease The minimum amount that can be deposited or reclaimed
    /// @param decisionTimeout The time window (in seconds) for the trustee to deny a reclaim request
    /// @dev Reverts if any of the arguments is zero
    constructor(uint16 netuid, address trustee, uint256 minCollateralIncrease, uint64 decisionTimeout) {
        // custom errors are not used here because it's a 1-time setup
        require(trustee != address(0), "Trustee address must be non-zero");
        require(minCollateralIncrease > 0, "Min collateral increase must be greater than 0");
        require(decisionTimeout > 0, "Decision timeout must be greater than 0");

        NETUID = netuid;
        TRUSTEE = trustee;
        MIN_COLLATERAL_INCREASE = minCollateralIncrease;
        DECISION_TIMEOUT = decisionTimeout;
    }

    modifier onlyTrustee() {
        if (msg.sender != TRUSTEE) {
            revert NotTrustee();
        }
        _;
    }

    // Allow deposits only via deposit() function
    receive() external payable {
        revert InvalidDepositMethod();
    }

    // Allow deposits only via deposit() function
    fallback() external payable {
        revert InvalidDepositMethod();
    }

    /// @notice Allows users to deposit collateral into the contract
    /// @dev The deposited amount must be greater than or equal to MIN_COLLATERAL_INCREASE
    /// @dev If it's not revert with InsufficientAmount error
    /// @dev Emits a Deposit event with the sender's address and deposited amount
    function deposit() external payable {
        if (msg.value < MIN_COLLATERAL_INCREASE) {
            revert InsufficientAmount();
        }

        collaterals[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// @notice Initiates a process to reclaim message sender's collateral from the contract
    /// @dev If it's not denied by the trustee, the collateral will be available for withdrawal after DECISION_TIMEOUT
    /// @dev The amount reclaimed must be greater than 0
    /// @dev The amount reclaimed must be greater than or equal to MIN_COLLATERAL_INCREASE untless it's a full collateral withdrawal
    /// @dev The total amount under pending reclaims cannot exceed the user's total collateral
    /// @param amount The amount of collateral to reclaim
    /// @param url URL containing information about the reclaim request
    /// @param urlContentMd5Checksum MD5 checksum of the content at the provided URL
    /// @dev Emits ReclaimProcessStarted event with reclaim details and timeout
    /// @dev Reverts with ReclaimAmountTooSmall if amount is 0 or doesn't meet minimum requirements
    /// @dev Reverts with ReclaimAmountTooLarge if there's insufficient collateral available
    function reclaimCollateral(uint256 amount, string calldata url, bytes16 urlContentMd5Checksum) external {
        if (amount == 0) {
            revert AmountZero();
        }

        uint256 collateral = collaterals[msg.sender];
        uint256 pendingCollateral = collateralUnderPendingReclaims[msg.sender];
        uint256 collateralAvailableForReclaim = collateral - pendingCollateral;
        if (pendingCollateral + amount > collateral) {
            revert ReclaimAmountTooLarge();
        }
        if (amount < MIN_COLLATERAL_INCREASE && collateralAvailableForReclaim != amount) {
            revert ReclaimAmountTooSmall();
        }

        uint64 expirationTime = uint64(block.timestamp) + DECISION_TIMEOUT;
        reclaims[++nextReclaimId] = Reclaim(msg.sender, amount, expirationTime);
        collateralUnderPendingReclaims[msg.sender] += amount;

        emit ReclaimProcessStarted(nextReclaimId, msg.sender, amount, expirationTime, url, urlContentMd5Checksum);
    }

    /// @notice Finalizes a reclaim request and transfers the collateral to the depositor if conditions are met
    /// @dev Can be called by anyone
    /// @dev Requires that deny timeout has expired
    /// @dev If the miner has been slashed and their collateral is insufficient for a reclaim, the reclaim is canceled but transactions completes successfully allowing to request another reclaim
    /// @param reclaimRequestId The ID of the reclaim request to finalize
    /// @dev Emits Reclaimed event with reclaim details if successful
    /// @dev Reverts with ReclaimNotFound if the reclaim request doesn't exist or was denied
    /// @dev Reverts with BeforeDenyTimeout if the deny timeout hasn't expired
    /// @dev Reverts with TransferFailed if the TAO transfer fails
    function finalizeReclaim(uint256 reclaimRequestId) external {
        Reclaim memory reclaim = reclaims[reclaimRequestId];
        if (reclaim.amount == 0) {
            revert ReclaimNotFound();
        }
        if (reclaim.denyTimeout >= block.timestamp) {
            revert BeforeDenyTimeout();
        }

        delete reclaims[reclaimRequestId];
        collateralUnderPendingReclaims[reclaim.miner] -= reclaim.amount;

        if (collaterals[reclaim.miner] < reclaim.amount) {
            // miner got slashed and can't withdraw
            return;
        }

        collaterals[reclaim.miner] -= reclaim.amount;

        emit Reclaimed(reclaimRequestId, reclaim.miner, reclaim.amount);

        // check-effect-interact pattern used to prevent reentrancy attacks
        (bool success,) = payable(reclaim.miner).call{value: reclaim.amount}("");
        if (!success) {
            revert TransferFailed();
        }
    }

    /// @notice Allows the trustee to deny a pending reclaim request before the timeout expires
    /// @dev Can only be called by the trustee (address set in constructor)
    /// @dev Must be called before the deny timeout expires
    /// @dev Removes the reclaim request and frees up the collateral for other reclaims
    /// @param reclaimRequestId The ID of the reclaim request to deny
    /// @param url URL containing the reason of denial
    /// @param urlContentMd5Checksum MD5 checksum of the content at the provided URL
    /// @dev Emits Denied event with the reclaim request ID
    /// @dev Reverts with NotTrustee if called by non-trustee address
    /// @dev Reverts with ReclaimNotFound if the reclaim request doesn't exist
    /// @dev Reverts with PastDenyTimeout if the timeout has already expired
    function denyReclaimRequest(uint256 reclaimRequestId, string calldata url, bytes16 urlContentMd5Checksum)
        external
        onlyTrustee
    {
        Reclaim memory reclaim = reclaims[reclaimRequestId];
        if (reclaim.amount == 0) {
            revert ReclaimNotFound();
        }
        if (reclaim.denyTimeout < block.timestamp) {
            revert PastDenyTimeout();
        }

        collateralUnderPendingReclaims[reclaim.miner] -= reclaim.amount;
        emit Denied(reclaimRequestId, url, urlContentMd5Checksum);

        delete reclaims[reclaimRequestId];
    }

    /// @notice Allows the trustee to slash a miner's collateral
    /// @dev Can only be called by the trustee (address set in constructor)
    /// @dev Removes the collateral from the miner and burns it
    /// @param miner The address of the miner to slash
    /// @param amount The amount of collateral to slash, must be greater than 0
    /// @dev Emits Slashed event with the miner's address and the amount slashed
    /// @dev Reverts with AmountZero if amount is 0
    /// @dev Reverts with InsufficientAmount if the miner has less collateral than the amount to slash
    /// @dev Reverts with TransferFailed if the TAO transfer fails
    function slashCollateral(address miner, uint256 amount, string calldata url, bytes16 urlContentMd5Checksum)
        external
        onlyTrustee
    {
        if (amount == 0) {
            revert AmountZero();
        }
        if (collaterals[miner] < amount) {
            revert InsufficientAmount();
        }
        collaterals[miner] -= amount;
        // burn the collateral
        (bool success,) = payable(address(0)).call{value: amount}("");
        if (!success) {
            revert TransferFailed();
        }

        emit Slashed(miner, amount, url, urlContentMd5Checksum);
    }
}
